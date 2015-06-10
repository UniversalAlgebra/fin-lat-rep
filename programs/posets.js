// Code by John Snow (at http://estrada.cune.edu/facweb/john.snow/drawlat.html)
// Modifications to draw several posets by Peter Jipsen (marked with //pj)

function drawPoset(poset,index,labels){
    var i,j;
    //e.g. poset = {0:[1,2,3],1:[4,5],2:[4,6],3:[5,6],4:[7],5:[7],6:[7],7:[]};
    // function continues near bottom of file

function dot(p){
	return (this.x*p.x+this.y*p.y+this.z*p.z);
	}
function norm(){
	return Math.sqrt(this.dot(this));
	}
function plus(b){
	c=new point(this.x+b.x, this.y+b.y, this.z+b.z);
	return(c);
	}
function sub(b){
	c=new point(this.x-b.x, this.y-b.y, this.z-b.z);
	return(c);
	}
function subXY(b){
	c=new point(this.x-b.x, this.y-b.y, this.z);
	return(c);
	}
function scale(s){
	c=new point(s*this.x, s*this.y, s*this.z);
	return(c);
	}
function zero(){
	this.x=0;
	this.y=0;
	this.z=0;
	}
function rand(n){
	this.x=Math.random() % n;
	this.y=Math.random() % n;
	this.z=Math.random() % n;

	}
function point(x,y,z){
	this.x=x;
	this.y=y;
	this.z=z;
	this.dot=dot;
	this.norm=norm;
	this.plus=plus;
	this.sub=sub;
	this.subXY=subXY;
	this.scale=scale;
	this.zero=zero;
	this.rand=rand;
	}
//**************************************************************/
//* 3D drawing stuff *******************************************/
var theCanvas;
var theContext;
var theForm;
var width;
var height;
var reachY=10;	
var reachX=10;		//maximum coordinate in DRAWING plane
var zoom=1.2;		        //zooming factor
var Pi=Math.PI;
var angleSteps=50;		//half number of rotation steps in //pj
					//one full revolution
var aStep=Pi/angleSteps;	//added to angle for rotation
var theta=0; 			//angle to eye from positive x-axis
var phi=0; 			//angle to eye from xy-plane
var projX;			//basis vectors for drawing plane
var projY;
var changed=0;			//flag to indicate if need redraw

function setProjectionMatrix(){
//set up basis for drawing plane
	projX.x=-Math.sin(theta);
	projX.y=Math.cos(theta);
	projX.z=0;
	projY.x=-Math.cos(theta)*Math.sin(phi);
	projY.y=-Math.sin(theta)*Math.sin(phi);
	projY.z= Math.cos(phi);
	}
function initProjectionMatrix(){
//begin with eye on positive x-axis
	projX=new point(0,0,0);
	projY=new point(0,0,0);
	theta=0;
	phi=0;
	setProjectionMatrix();
	}
function projectAndScaleX(p){
//find x-component of point on drawing plane
	return (width*(projX.dot(p)+reachX)/(2*reachX));
	}
function projectAndScaleY(p){
//find y-component of point on drawing plane
	return height-(height*(projY.dot(p)+reachY)/(2*reachY));
	}
function drawLine(p,q){
	theContext.beginPath();
	theContext.moveTo(projectAndScaleX(p), projectAndScaleY(p));
	theContext.lineTo(projectAndScaleX(q), projectAndScaleY(q));
	theContext.stroke();
	}
    function drawSphere(p, r, lab){
	theContext.beginPath();
        theContext.arc(projectAndScaleX(p), projectAndScaleY(p), r, 0, 2*Pi, false);
	theContext.fill();
	theContext.stroke(); //pj
        if (labels) 
            theContext.fillText(lab,projectAndScaleX(p),projectAndScaleY(p));
	}
//*****************************************************************/
//* drawLat Stuff ********************************************/

var tStep=0.01;		//time step
var N;				//number of elements in ordered set
var thePoints; 			//arrays for points, velocities, forces
var theForces;
var theGraph;			//graph of covering relation
var theOrder;			//order relation
var theHeights; 		//height
var theDepths;			//max height - depth
var sorted;			//elements are bubble sorted to find height
var radius=3;		        //pj pixel radius of ball drawn for each point
var improve=1;			//flag to indicate when forces applied
var repulsion=1;		//constants for proportional forces
var attraction=1;
var coverAttraction=1;
var minForces=0.05;             //min. sum of forces^2 when improve stops
var sumForces=1;                //current sum of forces^2
var goInterval;                 //used to clear the setInterval command
var label=null;

function drawGraph(){
	var x,y,i;

	theContext.fillStyle="white";
	theContext.fillRect(0,0,width,height);

	for (x=0;x<N;x++)
		for (y=0;y<N;y++)
			if (theGraph[x][y])
				drawLine(thePoints[x], thePoints[y]);
	for (x=0;x<N;x++)
	    drawSphere(thePoints[x], radius, label?label[x]:""+x);
	changed=0;
	theContext.fillStyle="black"; //pj
        theContext.textAlign="center"; //pj
	theContext.fillText("" + index, width / 2, height); //zj
	}
function findForces(){
	var i,j,d,l,r,a,tforce;
	r=2;
	a=1;
	for (i=0;i<N;i++)
		theForces[i].zero();
	for (i=0;i<N;i++)
		for (j=0;j<N;j++)
			if (i != j) {
			d=thePoints[j].sub(thePoints[i]);
			l=d.dot(d);
			//Attraction for covers
			if ((theGraph[i][j])){
				theForces[j].x-=((coverAttraction)*d.x);
				theForces[j].y-=((coverAttraction)*d.y);
				theForces[i].x+=((coverAttraction)*d.x);
				theForces[i].y+=((coverAttraction)*d.y);
				}
			//Attraction for comparables
			if ((theOrder[i][j])){
				theForces[j].x-=((attraction/l)*d.x);
				theForces[j].y-=((attraction/l)*d.y);
				theForces[i].x+=((attraction/l)*d.x);
				theForces[i].y+=((attraction/l)*d.y);
				}
			//Repulsion for incomparables
			else if (!(theOrder[j][i]) ){  //pj reversed i,j
				theForces[j].x+=((repulsion/l)*d.x);
				theForces[j].y+=((repulsion/l)*d.y);
				theForces[i].x-=((repulsion/l)*d.x);
				theForces[i].y-=((repulsion/l)*d.y);
				}
			}
        sumForces = 0;     //pj
	for (i=0;i<N;i++)  //pj
	    sumForces += theForces[i].dot(theForces[i]); //pj
	}
function updatePositions(){
//new position = old position + velocity * tStep
	var i;
	for (i=0;i<N;i++){
		thePoints[i].x+=tStep*theForces[i].x; //pj
		thePoints[i].y+=tStep*theForces[i].y; //pj
		}	
	}

function recenter(){
//translate points so CM is at orgin for zooming and rotation
	var i,j, c;
	c=new point(0,0,0);
	for (i=0;i<N;i++)
		c=c.plus(thePoints[i]);
	c=c.scale(1/N);
	for (i=0;i<N;i++)
		thePoints[i]=thePoints[i].subXY(c);
	}

var xpos = []; //pj temp lists for planar coordinates
var ypos = []; //pj

function bestAngle(){ // added by pj
    var a,i,j;
    var bestang = 0.0;
    var bestsep = 0;
    for (a=0;a<angleSteps;a++){
        theta += aStep;
		setProjectionMatrix();
        for (i=0;i<N;i++){
            xpos[i] = projX.dot(thePoints[i]);
            ypos[i] = projY.dot(thePoints[i]);
	}
        minsep = 1000;
        for (i=0;i<N;i++)
            for (j=i+1;j<N;j++)
                if (Math.abs(ypos[i]-ypos[j])<0.8 && 
                    Math.abs(xpos[i]-xpos[j])<minsep) 
                    minsep = Math.abs(xpos[i]-xpos[j]);
	if (minsep > bestsep && minsep != 1000){
            bestsep = minsep;
            bestang = theta;
	}
    }
    theta = bestang;
    setProjectionMatrix();
	
	
}
function rescaleX(){
	var maxX=0;
	var minX=1000;	
	var x;
	for (i=0;i<N;i++)
	{
		x = projX.dot(thePoints[i]);
		if (x > maxX)
			maxX=x;
		if (minX > x)
			minX=x;
	}
	if (maxX-minX >=reachX)
		reachX = maxX-minX;
}
function repositionZ(){
	var maxZ=0;
	var minZ=1000;	
	var z;
	for (i=0;i<N;i++)
	{
		z = thePoints[i].z;
		if (z > maxZ)
			maxZ=z;
		if (minZ > z)
			minZ=z;
	}
	for (i=0;i<N;i++)
		thePoints[i].z = thePoints[i].z - (maxZ + minZ) / 2.0;
}

function updatePoints(){
    findForces(); //pj
    updatePositions();
    recenter();
    drawGraph();
}
function transitiveClosure(){
	var i, x,y,z;
	for (i=0;i<N+1;i++)
	for (x=0;x<N;x++)
	for (y=0;y<N;y++)
	for (z=0;z<N;z++)
		theOrder[x][z]=theOrder[x][z] || (theOrder[x][y] && theOrder[y][z]);
	}
function bubbleSort(){
//bubble sort elements to find heights
	var x,y,t;
	for (x=0;x<N;x++)
		sorted[x]=x;
	for (x=0;x<N;x++)
		for (y=x+1;y<N;y++)
			if (theOrder[sorted[y]][sorted[x]]){
				t=sorted[y];
				sorted[y]=sorted[x];
				sorted[x]=t;
				}
	}
function findHeights(){
    var x,y;
    for (x=0;x<N;x++)
	theHeights[x]=0;
    for (x=0;x<N;x++)
	for (y=x+1;y<N;y++)
	    if (theGraph[sorted[x]][sorted[y]] && 
                theHeights[sorted[y]]<theHeights[sorted[x]]+1) //pj
		theHeights[sorted[y]]=theHeights[sorted[x]]+1;
}
function findDepths(){
    var m, x, y;
    m=0;
    for (x=0;x<N;x++)
	if (m<theHeights[x])
	    m=theHeights[x];

    reachY=(m+1)/zoom; //pj
    reachX=reachY;

    for (x=0;x<N;x++)
	theDepths[x]=m;
    for (y=N-1;y>=0;y--)
	for (x=y-1;x>=0;x--)
	    if (theGraph[sorted[x]][sorted[y]] && 
		theDepths[sorted[x]]>theDepths[sorted[y]]-1) //pj
		theDepths[sorted[x]]=theDepths[sorted[y]]-1; //pj Height->Depth
}
function findZs(){
	var x;
	for (x=0;x<N;x++)
		thePoints[x].z=(theHeights[x]+theDepths[x])/2;
	}
function centerSingles(){
//if there is exactly on maximal (minimal) element then
//its initial position is on the z-axis to help symmetry
	var i,j,h,n,max, min;

	for (i=0;i<N;i++){
		h=thePoints[i].z;
		n=0;
		max=1;
		min=1;
		for (j=0;j<N;j++){
			if (thePoints[j].z == h)
				n++;
			else if ((thePoints[j].z>h))
				max=0;
			else if ((thePoints[j].z<h))
				min=0;
			}
		if ((n==1) && ((max) || (min))){
			thePoints[i].x=0;
			thePoints[i].y=0;
			}
		}
	}
function initializeArrays(){
	var i,j,x,y;
	initProjectionMatrix();
	thePoints=new Array(N);
	theForces=new Array(N);
	theHeights=new Array(N);
	theDepths=new Array(N);
	sorted = new Array(N);
	for(i=0;i<N;i++){
		thePoints[i]=new point(0,0,0);
		theForces[i]=new point(0,0,0);
		}
	theGraph=new Array(N);
	for (i=0;i<N;i++)
		theGraph[i]=new Array(N);

	theOrder=new Array(N);
	for (i=0;i<N;i++)
		theOrder[i]=new Array(N);

	for (i=0;i<N;i++)
		for (j=0;j<N;j++){
			theGraph[i][j]=0;
			theOrder[i][j]=0;
			theOrder[i][i]=1;
			}
	}
//************************************************************/
//
function go(){
    if (sumForces>minForces) updatePoints();
    else {
	bestAngle();
	rescaleX();
	drawGraph();
	clearInterval(goInterval);
    }
}


//continue drawPoset
    canvas = document.getElementById("c" + index);//obtain canvas
    theContext = canvas.getContext("2d");
    width = canvas.width;
    height = canvas.height;

    initProjectionMatrix();
    if (label in poset) {
        N = Object.keys(poset).length-1;
        label = poset.label;
    }else{ 
        N = Object.keys(poset).length;
	label = null;
    }
    initializeArrays();
    //init cover graph
    for (i=0;i<N;i++){
	for (j=0;j < poset[i].length;j++){
	    theGraph[i][poset[i][j]]=1;
	    theOrder[i][poset[i][j]]=1;
	}
    }
    //initial positions are random
    for (i=0;i<N;i++)
	thePoints[i].rand(N);
    transitiveClosure();
    bubbleSort();
    findHeights();
    findDepths();
    findZs();
    centerSingles();
    recenter();
	repositionZ();
    goInterval = setInterval(go,1); //improvement loop: where computation happens
}
//***************************************************************/
// File must contain <canvas> tags for each poset, with ids c0,c1,c2,...
// See math.chapman.edu/~jipsen/posets/lattices77.html for an example

function drawPosets(posetList,labels){
    var i;
    for (i=0;i<posetList.length;i++) drawPoset(posetList[i],i,labels);
}