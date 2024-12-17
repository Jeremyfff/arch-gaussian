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

vec4 blend(vec4 bgColor, vec4 fgColor){
    vec4 c = mix(bgColor, fgColor, fgColor.a);
    float a = bgColor.a + fgColor.a - bgColor.a * fgColor.a;
    return vec4(c.rgb, a);
}


out vec4 fragColor;

uniform sampler2D geometry_color_texture;// vec4
uniform sampler2D gaussian_color_texture;// vec4

in vec2 uv0;

void main() {
    vec4 geometry_color = texture(geometry_color_texture, uv0);
    vec4 gaussian_color = texture(gaussian_color_texture, uv0);
    fragColor = blend(geometry_color, gaussian_color);
}
#endif
