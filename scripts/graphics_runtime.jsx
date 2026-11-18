    // Injected inside the bounded runtime; shares comp/layer/prop/readback helpers.
    function isGraphic(op) {
        return /^(radial_pattern|wave_grid|contour_pattern|scatter_pattern|text_pattern|motion_trail|stagger_layers)$/.test(op);
    }
    function deselect(c) {for(var n=1;n<=c.numLayers;n++)c.layer(n).selected=false;}
    function near(a,b) {
        if(a instanceof Array) {if(!(b instanceof Array)||a.length!==b.length)return false;for(var n=0;n<a.length;n++)if(!near(a[n],b[n]))return false;return true;}
        return typeof a==="number" && typeof b==="number" && Math.abs(a-b)<0.0001;
    }
    function gGroup(l,index) {return l.property("ADBE Root Vectors Group").property(index);}
    function gContents(l,index) {return gGroup(l,index).property("ADBE Vectors Group");}
    function contourExpression(item,a) {
        return "var pts=[],n=96,p="+item.phase+",t=2*Math.PI*time*"+a.speed+";\n"+
            "for(var i=0;i<n;i++){var q=i*2*Math.PI/n;var r="+item.radius+"+"+a.distortion+
            "*(0.62*Math.sin(3*q+p+t)+0.38*Math.sin(5*q-p-t));pts.push([r*Math.cos(q),r*Math.sin(q)]);}\n"+
            "createPath(pts,[],[],true);";
    }
    function contourShape(item,a) {
        var s=new Shape(),v=[];
        for(var n=0;n<96;n++) {
            var q=n*2*Math.PI/96,r=item.radius+a.distortion*(0.62*Math.sin(3*q+item.phase)+0.38*Math.sin(5*q-item.phase));
            v.push([r*Math.cos(q),r*Math.sin(q)]);
        }
        s.vertices=v;s.closed=true;
        var z=[];for(var j=0;j<v.length;j++)z.push([0,0]);s.inTangents=z;s.outTangents=z;
        return s;
    }
    function addGraphicGroup(l,item,a,index) {
        var root=l.property("ADBE Root Vectors Group"),group=root.addProperty("ADBE Vector Group"),gi=group.propertyIndex;
        group.name="Element "+(index+1);
        var contents=gContents(l,gi);
        // ExtendScript associates chained ternaries differently from modern JS.
        var pathMatch="ADBE Vector Shape - Group";
        if(item.kind==="ellipse")pathMatch="ADBE Vector Shape - Ellipse";
        else if(item.kind==="rectangle")pathMatch="ADBE Vector Shape - Rect";
        contents.addProperty(pathMatch);
        gContents(l,gi).addProperty(item.kind==="path"?"ADBE Vector Graphic - Stroke":"ADBE Vector Graphic - Fill");
        contents=gContents(l,gi);
        var shape=contents.property(1),style=contents.property(2);
        if(shape.matchName!==pathMatch)throw Error("Shape lookup mismatch: expected "+pathMatch+", found "+shape.matchName+" (kind="+item.kind+")");
        if(item.kind==="path") {
            shape.property("ADBE Vector Shape").setValue(contourShape(item,a));
            shape.property("ADBE Vector Shape").expression=contourExpression(item,a);
            style.property("ADBE Vector Stroke Color").setValue(item.color);
            style.property("ADBE Vector Stroke Width").setValue(item.stroke);
            style.property("ADBE Vector Stroke Opacity").setValue(100);
        } else {
            var sizeMatch=item.kind==="ellipse"?"ADBE Vector Ellipse Size":"ADBE Vector Rect Size",sizeProperty=shape.property(sizeMatch);
            if(!sizeProperty)throw Error("Missing "+sizeMatch+" in "+shape.matchName+"; requested "+pathMatch+"; element "+encode(item));
            sizeProperty.setValue(item.size);
            if(item.kind==="rectangle")shape.property("ADBE Vector Rect Roundness").setValue(Math.min(item.size[0],item.size[1])*0.2);
            style.property("ADBE Vector Fill Color").setValue(item.color);
            style.property("ADBE Vector Fill Opacity").setValue(100);
            var tr=gGroup(l,gi).property("ADBE Vector Transform Group");
            tr.property("ADBE Vector Position").setValue(item.position);
            tr.property("ADBE Vector Rotation").setValue(item.rotation);
            tr.property("ADBE Vector Group Opacity").setValue(item.opacity);
            if(a.op==="wave_grid")tr.property("ADBE Vector Position").expression=
                "value + [0,Math.sin(2*Math.PI*time*"+a.speed+"+"+item.phase+")*"+a.amplitude+"];";
        }
    }
    function readGraphicGroup(l,index,a,probe) {
        var contents=gContents(l,index),shape=contents.property(1),style=contents.property(2),row;
        if(shape.matchName==="ADBE Vector Shape - Group") {
            var p=shape.property("ADBE Vector Shape"),now=p.valueAtTime(0,false),future=p.valueAtTime(probe,false);
            return {kind:"path",vertices:now.vertices.length,first_vertex:now.vertices[0],probe_vertex:future.vertices[0],
                color:style.property("ADBE Vector Stroke Color").value,stroke:style.property("ADBE Vector Stroke Width").value,
                expression_error:p.expressionError};
        }
        var ellipse=shape.matchName==="ADBE Vector Shape - Ellipse",tr=gGroup(l,index).property("ADBE Vector Transform Group"),pos=tr.property("ADBE Vector Position");
        row={kind:ellipse?"ellipse":"rectangle",size:shape.property(ellipse?"ADBE Vector Ellipse Size":"ADBE Vector Rect Size").value,
            position:pos.valueAtTime(0,false),probe_position:pos.valueAtTime(probe,false),rotation:tr.property("ADBE Vector Rotation").value,
            color:style.property("ADBE Vector Fill Color").value,opacity:tr.property("ADBE Vector Group Opacity").value,expression_error:pos.expressionError};
        return row;
    }
    function makeShapeGraphic(a,c,r) {
        var names={radial_pattern:"Laya Radial",wave_grid:"Laya Wave Grid",contour_pattern:"Laya Contours",scatter_pattern:"Laya Scatter"};
        var l=c.layers.addShape();l.name=names[a.op]+" · seed "+a.seed;l.inPoint=0;l.outPoint=c.duration;
        prop(l,"anchor_point").setValue(nativeValue(prop(l,"anchor_point"),[0,0],l));
        prop(l,"position").setValue(nativeValue(prop(l,"position"),[c.width/2,c.height/2],l));
        for(var n=0;n<a.items.length;n++)addGraphicGroup(l,a.items[n],a,n);
        if(a.spin)prop(l,"rotation").expression="value + time * "+a.spin+";";
        l.comment="LAYA "+a.op+" | seed "+a.seed+" | editable Contents groups";
        var probe=Math.min(1,c.duration/3);
        r.items=[];for(var i=1;i<=l.property("ADBE Root Vectors Group").numProperties;i++)r.items.push(readGraphicGroup(l,i,a,probe));
        r.created_layer_ids=[l.id];r.added_layers=1;r.element_count=r.items.length;
        r.layer_position=visibleValue(prop(l,"position").value,l);r.layer_rotation_probe=prop(l,"rotation").valueAtTime(probe,false);
        deselect(c);l.selected=true;
        return r;
    }
    function makeTextGraphic(a,c,r) {
        var made=[],item,l,p,d,rect;
        for(var n=a.items.length-1;n>=0;n--) {
            item=a.items[n];l=c.layers.addText(item.text);l.name="Laya Text "+("00"+(n+1)).slice(-3);
            l.inPoint=0;l.outPoint=c.duration;
            p=l.property("ADBE Text Properties").property("ADBE Text Document");d=p.value;
            d.fontSize=item.font_size;d.applyFill=true;d.applyStroke=false;d.fillColor=item.color;
            d.justification=ParagraphJustification.CENTER_JUSTIFY;p.setValue(d);
            rect=l.sourceRectAtTime(0,false);
            prop(l,"anchor_point").setValue(nativeValue(prop(l,"anchor_point"),[rect.left+rect.width/2,rect.top+rect.height/2],l));
            prop(l,"position").setValue(nativeValue(prop(l,"position"),item.position,l));prop(l,"rotation").setValue(item.rotation);
            l.comment="LAYA text_pattern | tile "+(n+1);made[n]=l;
        }
        r.items=[];r.created_layer_ids=[];deselect(c);
        for(var i=0;i<made.length;i++) {
            l=made[i];d=l.property("ADBE Text Properties").property("ADBE Text Document").value;
            r.items.push({position:visibleValue(prop(l,"position").value,l),rotation:prop(l,"rotation").value,text:d.text,font_size:d.fontSize,color:d.fillColor});
            r.created_layer_ids.push(l.id);l.selected=true;
        }
        r.added_layers=made.length;r.element_count=made.length;return r;
    }
    function makeTrails(a,c,r) {
        var source=layer(c,a.layer),made=[],previous=source;
        if(source.threeDLayer || prop(source,"position").dimensionsSeparated)throw Error("Trails require an unsplit 2D source");
        var names={position:"position",anchor_point:"anchorPoint",scale:"scale",rotation:"rotation",opacity:"opacity"};
        for(var i=1;i<=a.count;i++) {
            var copy=source.duplicate();copy.name=source.name+" · Trail "+("00"+i).slice(-2);copy.moveAfter(previous);previous=copy;
            var controlName="Laya Trail Source "+job.job_id.substring(0,8)+" "+i;
            var effect=copy.property("ADBE Effect Parade").addProperty("ADBE Layer Control");effect.name=controlName;effect.property(1).setValue(source.index);
            var expressions={},delay=i*a.delay,decay=Math.pow(a.decay,i);
            for(var name in names)if(names.hasOwnProperty(name)) {
                var expression="var s=effect("+encode(controlName)+")(1); s.transform."+names[name]+".valueAtTime(time-"+delay+")"+(name==="opacity"?"*"+decay:"")+";";
                prop(copy,name).expression=expression;expressions[name]=expression;
            }
            copy.comment="LAYA motion_trail | source ID "+source.id+" | delay "+delay;
            made.push({layer:copy,control:controlName,expressions:expressions,delay:delay,decay:decay});
        }
        r.trails=[];r.created_layer_ids=[];
        var sample=Math.min(c.duration-0.001,a.count*a.delay+1);
        for(var j=0;j<made.length;j++) {
            var entry=made[j],l=entry.layer,ok=true,samples=true;
            for(var key in names)if(names.hasOwnProperty(key)) {
                var p=prop(l,key),sourceProp=prop(source,key),actual=p.valueAtTime(sample,false),sampleOK=false;
                if(!p.expressionEnabled || p.expressionError || p.expression!==entry.expressions[key])ok=false;
                // Scripting and expression time subtraction may round on opposite
                // sides of AE's 1/1024-frame subframe tick. Check that tick only.
                for(var tick=-1;tick<=1;tick++) {
                    var wanted=sourceProp.valueAtTime(sample-entry.delay+tick*c.frameDuration/1024,false);
                    if(key==="opacity")wanted*=entry.decay;
                    if(near(actual,wanted))sampleOK=true;
                }
                if(!sampleOK)samples=false;
            }
            var linkedIndex=l.property("ADBE Effect Parade").property(entry.control).property(1).value;
            r.trails.push({source_id:c.layer(linkedIndex).id,delay:entry.delay,decay:entry.decay,expressions_ok:ok,sample_matches:samples});
            r.created_layer_ids.push(l.id);
        }
        deselect(c);source.selected=true;r.added_layers=made.length;return r;
    }
    function easeEntrance(p) {
        for(var n=1;n<=2;n++) {
            p.setInterpolationTypeAtKey(n,KeyframeInterpolationType.BEZIER,KeyframeInterpolationType.BEZIER);
            p.setTemporalEaseAtKey(n,[new KeyframeEase(0,66)],[new KeyframeEase(0,66)]);
        }
    }
    function checkEntranceEase(p) {
        for(var n=1;n<=2;n++)if(p.keyInInterpolationType(n)!==KeyframeInterpolationType.BEZIER || p.keyOutInterpolationType(n)!==KeyframeInterpolationType.BEZIER || Math.abs(p.keyOutTemporalEase(n)[0].influence-66)>0.001)return false;
        return true;
    }
    function staggerGraphic(a,c,r) {
        var targets=[];
        // Validate every target before adding the first keyframe.
        for(var i=0;i<a.layers.length;i++) {
            var l=layer(c,a.layers[i]),p=prop(l,"position"),o=prop(l,"opacity"),start=a.start+i*a.delay;
            if(l.threeDLayer || p.dimensionsSeparated || p.numKeys || o.numKeys || p.expressionEnabled || o.expressionEnabled)throw Error("Stagger preserves existing animation; use static unsplit 2D layers");
            if(start<l.inPoint || start+a.duration>Math.min(c.duration,l.outPoint))throw Error("Stagger keys exceed layer duration");
            targets.push({layer:l,position:visibleValue(p.value,l),opacity:o.value,start:start});
        }
        r.stagger=[];r.created_layer_ids=[];r.added_layers=0;
        for(var j=0;j<targets.length;j++) {
            var row=targets[j],target=row.layer,position=prop(target,"position"),opacity=prop(target,"opacity");
            var initial=[row.position[0],row.position[1]+a.offset];
            position.setValueAtTime(row.start,nativeValue(position,initial,target));position.setValueAtTime(row.start+a.duration,nativeValue(position,row.position,target));
            opacity.setValueAtTime(row.start,0);opacity.setValueAtTime(row.start+a.duration,row.opacity);
            easeEntrance(position);easeEntrance(opacity);
            var first=visibleValue(position.keyValue(1),target),last=visibleValue(position.keyValue(2),target);
            r.stagger.push({layer_id:target.id,times:[position.keyTime(1),position.keyTime(2)],opacity_times:[opacity.keyTime(1),opacity.keyTime(2)],offset:first[1]-last[1],
                initial_opacity:opacity.keyValue(1),original_position:row.position,final_position:last,original_opacity:row.opacity,
                final_opacity:opacity.keyValue(2),easing_ok:checkEntranceEase(position)&&checkEntranceEase(opacity)});
        }
        return r;
    }
    function executeGraphic(a) {
        var c=comp(a.comp),r={op:a.op,comp_id:c.id};
        if(c.width!==a.width || c.height!==a.height || Math.abs(c.duration-a.comp_duration)>0.0001)throw Error("Graphic target dimensions/duration changed");
        if(c.numLayers+a.added_layers>200)throw Error("Graphics require at most 200 layers after execution");
        if(a.op==="motion_trail") {r.layer_id=layer(c,a.layer).id;return makeTrails(a,c,r);}
        if(a.op==="stagger_layers")return staggerGraphic(a,c,r);
        if(a.op==="text_pattern")return makeTextGraphic(a,c,r);
        return makeShapeGraphic(a,c,r);
    }
