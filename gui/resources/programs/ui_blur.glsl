#version 330
precision highp float;
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

uniform sampler2D _Texture;
uniform vec2 _Dir;
uniform float _Radius;

uniform float _K_Y;  // radius_scalar_y = _K_Y * y + _B_Y; default: 0
uniform float _B_Y;  //                                    default: 1
uniform float _K_X;  // radius_scalar_x = _K_X * x + _B_X; default: 0
uniform float _B_X;  //                                    default: 1
uniform vec4 _Tint0; // color tint when radius_scalar_x * radius_scalar_y == 0
uniform vec4 _Tint1; // color tint when radius_scalar_x * radius_scalar_y == 1

const int M = 16;
const int N = 2 * M + 1;
const float SIGMA = 16.0 / 3.0;

#define PI 3.14159265
float getGaussianWeight(float x)
{
    float weight =  exp(-x * x / (2.0 * SIGMA * SIGMA)) / (sqrt(2.0 * 3.141592653589793) * SIGMA);
    return weight;
}
vec4 lerp(vec4 a, vec4 b, float t) {
    return a + (b - a) * t;
}


void main()
{
    float radius_scalar_y = _K_Y * uv0.y + _B_Y;
    float radius_scalar_x = _K_X * uv0.x + _B_X;
    radius_scalar_y = clamp(radius_scalar_y, 0.0, 1.0);
    radius_scalar_x = clamp(radius_scalar_x, 0.0, 1.0);
    float t = radius_scalar_x * radius_scalar_y;
    t = t * 2.0 - 1.0;
    t = t * PI * 0.5;
    t = sin(t); // -1 to 1
    t = t * 0.5 + 0.5; // 0 to 1
    float radius = _Radius * t;
    vec4 tint = lerp(_Tint0, _Tint1, t);

    vec4 sum = vec4(0.0);

    for (int i = 0; i < N; ++i)
    {
        float weight = getGaussianWeight(float(i - M));
        vec2 tc = uv0 + _Dir * float(i - M) * radius / M;
        tc = clamp(tc, 0.01, 0.99);
        sum += weight * texture(_Texture, tc);
    }

    vec4 blurred_color = clamp(sum, 0.0, 1.0);
    fragColor = lerp(blurred_color, tint, tint.a);
}
#endif
