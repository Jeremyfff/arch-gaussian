#version 330

#if defined VERTEX_SHADER

in vec3 in_position;
in vec2 in_texcoord_0;
out vec2 uv0;

void main() {
    gl_Position = vec4(in_position, 1);
    uv0 = in_texcoord_0;
}

#elif defined FRAGMENT_SHADER

in vec2 uv0;
out vec4 fragColor;

uniform float iTime;
uniform vec2  iResolution;
// A lot of spheres. Created by Reinder Nijhoff 2013
// Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
// @reindernijhoff
// 
// https://www.shadertoy.com/view/lsX3WH
//

#define SHADOW
#define REFLECTION

#define RAYCASTSTEPS 40

#define GRIDSIZE 10.
#define GRIDSIZESMALL 7.
#define MAXHEIGHT 30.
#define SPEED 18.
#define FPS 60.
#define MAXDISTANCE 260.
#define EPSILON 0.0001


#define HASHSCALE1 .1031
#define HASHSCALE3 vec3(.1031, .1030, .0973)
#define HASHSCALE4 vec4(1031, .1030, .0973, .1099)

vec3 pal( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d ) {
    return a + b*cos( 6.28318*(c*t+d) );
}

vec3 getCol( in float t ) {
	return pal(t, vec3(0.5,0.5,0.5),vec3(0.5,0.5,0.5),vec3(1.0,1.0,1.0),vec3(0.0,0.10,0.20) );
}

//
// math functions
//

//----------------------------------------------------------------------------------------
//  1 out, 2 in...
float hash12(vec2 p) {
	vec3 p3  = fract(vec3(p.xyx) * HASHSCALE1);
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.x + p3.y) * p3.z);
}


//----------------------------------------------------------------------------------------
///  2 out, 2 in...
vec2 hash22(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * HASHSCALE3);
    p3 += dot(p3, p3.yzx+19.19);
    return fract(vec2((p3.x + p3.y)*p3.z, (p3.x+p3.z)*p3.y));
}

//
// intersection functions
//

bool intersectPlane(vec3 ro, vec3 rd, float height, out float dist) {	
	if (rd.y==0.0) {
		return false;
	}
	
	float d = -(ro.y - height)/rd.y;
	d = min(100000.0, d);
	if( d > 0. ) {
		dist = d;
		return true;
	}
	return false;
}

bool intersectUnitSphere ( in vec3 ro, in vec3 rd, in vec3 sph, out float dist, out vec3 normal ) {
	vec3  ds = ro - sph;
	float bs = dot( rd, ds );
	float cs = dot(  ds, ds ) - 1.0;
	float ts = bs*bs - cs;
	
	if( ts > 0.0 ) {
		ts = -bs - sqrt( ts );
		if( ts>0. ) {
			normal = normalize( (ro+ts*rd)-sph );
			dist = ts;
			return true;
		}
	}
	
	return false;
}


//
// Scene
//

void getSphereOffset( const in vec2 grid, inout vec2 center ) {
	center = (hash22( grid ) - vec2(0.5) )*(GRIDSIZESMALL);
}

void getMovingSpherePosition( const in vec2 grid, const in vec2 sphereOffset, inout vec3 center ) {
	// falling?
	float s = 0.1+hash12( grid );
    
	float t = fract(14.*s + iTime/s*.3);	
	float y =  s * MAXHEIGHT * abs( 4.*t*(1.-t) );
    
	vec2 offset = grid + sphereOffset;
	
	center = vec3(  offset.x + 0.5*GRIDSIZE, 1. + y, offset.y + 0.5*GRIDSIZE );
}

void getSpherePosition( const in vec2 grid, const in vec2 sphereOffset, inout vec3 center ) {
	vec2 offset = grid + sphereOffset;
	center = vec3( offset.x + 0.5*GRIDSIZE, 1., offset.y + 0.5*GRIDSIZE );
}

vec3 getSphereColor( vec2 grid ) {
	float m = hash12( grid.yx );
	return getCol(m);
}

vec3 trace(vec3 ro, vec3 rd, out vec3 intersection, out vec3 normal, out float dist, out int material) {
	material = 0; // sky
	dist = MAXDISTANCE;
	float distcheck;
	
	vec3 sphereCenter, col, normalcheck;
	
	if( intersectPlane( ro,  rd, 0., distcheck) && distcheck < MAXDISTANCE ) {
		dist = distcheck;
		material = 1;
		normal = vec3( 0., 1., 0. );
		col = getCol( 0.5 );
	} else {
		col = vec3( 0. );
	}
	
		
	// trace grid
	vec3 pos = floor(ro/GRIDSIZE)*GRIDSIZE;
	vec3 ri = 1.0/rd;
	vec3 rs = sign(rd) * GRIDSIZE;
	vec3 dis = (pos-ro + 0.5  * GRIDSIZE + rs*0.5) * ri;
	vec3 mm = vec3(0.0);
	vec2 offset;
		
	for( int i=0; i<RAYCASTSTEPS; i++ )	{
		if( material > 1 || distance( ro.xz, pos.xz ) > dist+GRIDSIZE ) break;
		vec2 offset;
		getSphereOffset( pos.xz, offset );
		
		getMovingSpherePosition( pos.xz, -offset, sphereCenter );
		
		if( intersectUnitSphere( ro, rd, sphereCenter, distcheck, normalcheck ) && distcheck < dist ) {
			dist = distcheck;
			normal = normalcheck;
			material = 2;
		}
		
		getSpherePosition( pos.xz, offset, sphereCenter );
		if( intersectUnitSphere( ro, rd, sphereCenter, distcheck, normalcheck ) && distcheck < dist ) {
			dist = distcheck;
			normal = normalcheck;
			col = getSphereColor( offset );
			material = 3;
		}
		mm = step(dis.xyz, dis.zyx);
		dis += mm * rs * ri;
		pos += mm * rs;		
	}
	
	vec3 color = vec3( 0. );
	if( material > 0 ) {
		intersection = ro + rd*dist;
		vec2 map = floor(intersection.xz/GRIDSIZE)*GRIDSIZE;
		
		if( material == 1 || material == 3 ) {
			// lightning
			vec3 c = vec3( -GRIDSIZE,0., GRIDSIZE );
			for( int x=0; x<3; x++ ) {
				for( int y=0; y<3; y++ ) {
					vec2 mapoffset = map+vec2( c[x], c[y] );		
					vec2 offset;
					getSphereOffset( mapoffset, offset );
					vec3 lcolor = getSphereColor( mapoffset ) * 5.;
					vec3 lpos;
					getMovingSpherePosition( mapoffset, -offset, lpos );
					
					float shadow = 1.;
#ifdef SHADOW
					if( material == 1 ) {
						for( int sx=0; sx<3; sx++ ) {
							for( int sy=0; sy<3; sy++ ) {
								if( shadow < 1. ) continue;
								
								vec2 smapoffset = map+vec2( c[sx], c[sy] );		
								vec2 soffset;
								getSphereOffset( smapoffset, soffset );
								vec3 slpos, sn;
								getSpherePosition( smapoffset, soffset, slpos );
								float sd;
								if( intersectUnitSphere( intersection, normalize( lpos - intersection ), slpos, sd, sn )  ) {
									shadow = 0.;
								}							
							}
						}
					}
#endif
					color += col * lcolor * ( shadow * max( dot( normalize(lpos-intersection), normal ), 0.) *
											 clamp(10. / dot( lpos - intersection, lpos - intersection) - 0.075, 0., 1.)  );
				}
			}
		} else {
			// emitter
			color = (4.+2.*dot(normal, vec3( 0.5, 0.5, -0.5))) * getSphereColor( map );
		}
	}
	return color;
}

void path( in float time, out vec3 ro, out vec3 ta ) {
	ro = vec3( 16.0*cos(0.2+0.5*.4*time*1.5) * SPEED, 10.0+5.*cos(time), 16.0*sin(0.1+0.5*0.11*time*1.5) * SPEED);
    time += 1.6;
	ta = vec3( 16.0*cos(0.2+0.5*.4*time*1.5) * SPEED, -20.0 + 10.*sin(time), 16.0*sin(0.1+0.5*0.11*time*1.5) * SPEED);
}

mat3 setCamera(in float time, out vec3 ro )
{
    vec3 ta;
    
    path(time, ro, ta);
	float roll = -0.15*sin(.732*time) * 0;

	vec3 cw = normalize(ta-ro);
	vec3 cp = vec3(sin(roll), cos(roll), 0.);
	vec3 cu = normalize( cross(cw,cp) );
	vec3 cv = normalize( cross(cu,cw) );
    return mat3( cu, cv, cw );
}

void main() {
	vec2 q = gl_FragCoord.xy/iResolution.xy;
	vec2 p = -1.0+2.0*q;
	p.x *= iResolution.x/iResolution.y;
	p.y *= -1;

// camera	
	vec3 ro0, ro1, ta;
    
    mat3 ca0 = setCamera( iTime - 1./30., ro0 );
	vec3 rd0 = ca0 * normalize( vec3(p.xy,2.0) );

    mat3 ca1 = setCamera( iTime, ro1 );
	vec3 rd1 = ca1 * normalize( vec3(p.xy,2.0) );
	        
    mat3 rot = ca1 * mat3( ca0[0].x, ca0[1].x, ca0[2].x,
                           ca0[0].y, ca0[1].y, ca0[2].y,
                           ca0[0].z, ca0[1].z, ca0[2].z);
    
    rot -= mat3( 1,0,0, 0,1,0, 0,0,1);
    
	// raytrace	
	vec3 ro = ro0;
    vec3 rd = rd0;


	// raytrace
	int material;
	vec3 normal, intersection;
	float dist;
	
	vec3 col = trace(ro, rd, intersection, normal, dist, material);

#ifdef REFLECTION
	if( material > 0 ) {
    	float f = 0.04 * clamp(pow(1. + dot(rd, normal), 5.), 0., 1.);
    	    
		vec3 ro = intersection + EPSILON*normal;
		rd = reflect( rd, normal );
		vec3 refColor = trace(ro, rd, intersection, normal, dist, material);
		if (material > 2) { 
    		col += 0.75 * refColor; 
		} else { // fresnell on floor
		    col += f * refColor;
		}
	}
#endif
	
	col = pow( col * .5, vec3(1./2.2) );	
	col = mix(col, smoothstep(vec3(0), vec3(1), col), .25);
	
	// vigneting
	col *= 0.25+0.75*pow( 16.0*q.x*q.y*(1.0-q.x)*(1.0-q.y), 0.15 );
	
	fragColor = vec4( col,1.0);
}

#endif
