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
#define PI 3.14159265358979323846
#define HIGHLIGHT_INTENSITY 0.2
#define HIGHLIGHT_POW 5
#define HIGHLIGHT_BOUNCE_SPEED 3
#define HIGHLIGHT_LOOP_SPEED 2
#define GAMMA 2.2

out vec4 fragColor;
in vec2 uv0;

uniform float _T;  // time
uniform float _Rounding;  // in pixel
uniform vec2 _Resolution; // in pixel
uniform float _Progress; // 0 to 1

uniform vec4 _BgColor;
uniform vec4 _BarColor;

uniform float _IsPreparing;
uniform float _IsRunning;

// ====================================================

float smoothedge(float v) {
    return smoothstep(-1.0 / _Resolution.x, 0.0, v);
}

float RoundRect(vec2 p, vec2 size, float radius) {
  vec2 d = abs(p) - size;
  return min(max(d.x, d.y), 0.0) + length(max(d,0.0))- radius;
}
vec4 blend(vec4 bgColor, vec4 fgColor){
    vec4 c = mix(bgColor, fgColor, fgColor.a);
    float a = bgColor.a + fgColor.a - bgColor.a * fgColor.a;
    return vec4(c.rgb, a);
}

vec4 lerp(vec4 a, vec4 b, float t) {
    return a + (b - a) * t;
}
float lerp(float a, float b, float t) {
    return a + (b - a) * t;
}

void main()
{

    vec2 st = gl_FragCoord.xy / _Resolution.x;
    float sizey_half = _Resolution.y / _Resolution.x / 2.0;
    float bar_sizey_half = sizey_half * 0.9;
    float radius = min(bar_sizey_half, _Rounding / _Resolution.x);

    float d = RoundRect(
        st - vec2(0.5, sizey_half),
        vec2(0.5 - radius, bar_sizey_half - radius),
        radius
    );
    float bg_mask = 1 - smoothedge(d);

    d = RoundRect(
        st - vec2(_Progress * ( 0.5 - radius) + radius, sizey_half),
        vec2(_Progress * (0.5 - radius), bar_sizey_half - radius),
        radius
    );

    float bar_mask = 1 - smoothedge(d);

    float highlight_bounce = sin(sin(_T * HIGHLIGHT_BOUNCE_SPEED) * PI * 0.5 + st.x * PI) * 0.5 + 0.5;
    float highlight_loop = sin(-_T * HIGHLIGHT_LOOP_SPEED + st.x * PI) * 0.5 + 0.5;
    float highlight = lerp(highlight_loop, highlight_bounce, _IsPreparing);
    highlight = pow(highlight, HIGHLIGHT_POW);

    vec4 bg_color = clamp(vec4(_BgColor.rgb * (1 + HIGHLIGHT_INTENSITY * _IsPreparing * highlight), _BgColor.a * bg_mask), 0.0, 1.0);
    vec4 bar_color = clamp(vec4(_BarColor.rgb * (1 + HIGHLIGHT_INTENSITY * highlight), _BarColor.a * bar_mask * _IsRunning), 0.0, 1.0);

    fragColor = blend(bg_color, bar_color);
    fragColor.a = pow(fragColor.a, 1 / GAMMA);
}
#endif
