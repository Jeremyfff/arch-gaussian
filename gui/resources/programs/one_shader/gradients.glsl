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

out vec4 fragColor;
in vec2 uv0;

// region uniform variables
uniform float iTime;
uniform vec2  iResolution;

uniform float _Temporal;    //value=0.1, min=0, max=1, step=0.01
uniform float _Spatial;     //value=2, min=0, max=4, step=0.01
uniform float _GX;          //value=0, min=0, max=1, step=0.01
uniform float _GY;          //value=0.1, min=0, max=1, step=0.01
uniform float _GZ;          //value=0.2, min=0, max=1, step=0.01
uniform float _Gradient;    //value=0.3, min=0, max=1, step=0.01
// endregion

#define m4  mat4( 0.00, 0.80, 0.60, -0.4, -0.80,  0.36, -0.48, -0.5, -0.60, -0.48, 0.64, 0.2, 0.40, 0.30, 0.20,0.4)
vec4 twistedSineNoise(vec4 q)
{
	float a = 1.;
	float f = 1.;
	vec4 sum = vec4(0);
	for(int i = 0; i < 3 ; i++){
		q = m4 * q;
		vec4 s = sin( q.ywxz * f) / f;
		q += s;
		sum += s;
		f *= 1.618;
	}
	return sum;
}
vec3 gradient( in float t)
{
    return .5 + .5*cos( 6.28318*(t+ vec3(_GX, _GY, _GZ)) );
}
float hash12(vec2 p)
{
	vec3 p3  = fract(vec3(p.xyx) * .1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}


void main()
{
    //https://oneshader.net/shader/7d773abf5a
    float t = iTime * _Temporal;
    vec3 c = vec3(0.);

    for(int y = 0; y < 2; y++){
      for(int x = 0; x < 2; x++){
            vec2 uv = ( gl_FragCoord.xy + vec2(x,  y) * 0.5) /iResolution.y;

            vec4 qa = vec4(uv * _Spatial, 10., t);
            vec4 a = twistedSineNoise(qa);
            vec4 ia = step(a, vec4(0.));

            vec4 qb = vec4(uv * _Spatial * 1.618, 20., -t);
            vec4 b = twistedSineNoise(qb);
            vec4 ib = step(b, vec4(0.));

            vec4 n = mod( ia +ib , vec4(2.));

            float i = dot(n, vec4(1, 2,4,8));
            c +=  gradient(i/ 16. + uv.x * _Gradient );
        }
    }
    c = sqrt(c * .25);
    c += hash12( gl_FragCoord.xy) * 0.075;
    fragColor = vec4(c, 1.);
}
#endif
