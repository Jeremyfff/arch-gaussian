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

uniform float iTime;
//uniform vec2  iResolution;

uniform float _RotZoom; // value=0.12, min=0, max=1, step=0.01
uniform float _DistStep; // value=0.005, min=0, max=0.02, step=0.0001
uniform vec4  _Color; // value=1, .25, .8


void main() {
    float t = iTime / 4.;
    vec2 I = gl_FragCoord.xy;
    vec2 vScreen = uv0 * 2 - 1;
    vec3 d = -.2 * vec3(vScreen, 1.),
         c = vec3(0);

    float dist = 0.;

    for (int x = 0; x < 50; ++x) {
        vec3 p = c;

        p.z -= t + (dist += _DistStep);
        p.xy *= mat2( sin( (p.z *= _RotZoom) + vec4(0, 11, 20, 0)) );

        c += length(sin(p.yx) + cos(p.xz + t)) * d;
    }

    fragColor.rgb = 2.5 * _Color.rgb / length(c);
    fragColor.a = 1.;
}
#endif
