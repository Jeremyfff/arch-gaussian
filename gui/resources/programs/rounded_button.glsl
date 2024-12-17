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

uniform float _T;
uniform float _Rounding;  // in pixel
uniform vec2 _Resolution; // in pixel

float smoothedge(float v) {
    return smoothstep(0.0, 1.0 / _Resolution.x, v);
}

float RoundRect(vec2 p, vec2 size, float radius) {
  vec2 d = abs(p) - size;
  return min(max(d.x, d.y), 0.0) + length(max(d,0.0))- radius;
}

float Ellipse(vec2 p, vec2 r, float s) {
    return (length(p / r) - s);
}

void main()
{

    vec2 st = gl_FragCoord.xy / _Resolution.x;
    float sizey_half = _Resolution.y / _Resolution.x / 2.0;
    float radius = min(sizey_half, _Rounding / _Resolution.x);

    float rect = RoundRect(
        st - vec2(0.5, sizey_half),
        vec2(0.5 - radius, sizey_half - radius),
        radius
    );
    rect = 1 - smoothedge(rect);


    float ellipse = Ellipse(
        st - vec2(0, sizey_half), // center
        vec2(1, sizey_half * 1.15), // half radius
        1
    );

    ellipse = smoothstep(1, -0.35, ellipse);
    float mask = rect * ellipse;

    float l = smoothstep(_T, _T * 1.1 - 1, st.x);  // 0 to 1 lerp
    float alpha = l * mask;
//    alpha = pow(alpha, 1 / 2.2);
    fragColor = vec4(1, 1, 1, alpha);

}
#endif
