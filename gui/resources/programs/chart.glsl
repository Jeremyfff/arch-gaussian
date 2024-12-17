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

uniform sampler2D _DataTex;
uniform vec2 _Resolution;
uniform float _Capacity;
uniform float _DataMin;
uniform float _DataMax;
uniform vec4 _ColorMin;
uniform vec4 _ColorMax;
uniform vec4 _ColorLine;
uniform float _NumUndefinedData;

vec4 lerp(vec4 a, vec4 b, float t) {
    return a + (b - a) * t;
}

float remap_data(float data){
    data = clamp((data - _DataMin) / (_DataMax - _DataMin), 0.0, 1.0);// it should between 0 to 1
    return data;
}
float get_sample_x(float x, float data_size_x){
    return x * (1 - data_size_x) + data_size_x / 2.0;
}
void main()
{
    vec2 st = gl_FragCoord.xy / _Resolution.xy;
    st.y = 1 - st.y;

    if(st.x < (_NumUndefinedData) / (_Capacity - 1)){
        fragColor = vec4(.0);
        return;
    }
    float data_size_x = 1.0 / _Capacity;
    float pixel_size_x = 1.0 / _Resolution.x;

//    st.x = max(st.x, data_size_x);
//    st.x = min(st.x, 1 - data_size_x);

    float data = remap_data(texture(_DataTex, vec2(get_sample_x(st.x, data_size_x), 0.5)).r);// it should between 0 to 1
    float data_l = remap_data(texture(_DataTex, vec2(get_sample_x(max(st.x - pixel_size_x, 0), data_size_x), 0.5)).r);
    float data_r = remap_data(texture(_DataTex, vec2(get_sample_x(min(st.x + pixel_size_x, 1), data_size_x), 0.5)).r);
    float k = (data_r - data_l) / (2 * pixel_size_x);


    float mask = 1 - smoothstep(data, data + pixel_size_x, st.y);
    float line_width = 5 * sqrt(1 + k * k);
    float line_mask = (1 - smoothstep(data - (line_width-1) * pixel_size_x, data - (line_width) * pixel_size_x, st.y)) * mask;

    vec4 fill_color = lerp(_ColorMin, _ColorMax, st.y);
    fill_color.a *= mask;

    vec4 line_color = _ColorLine;

    fragColor = lerp(fill_color, line_color, line_mask);
    fragColor.a = pow(fragColor.a, 1 / 2.2);
}
#endif
