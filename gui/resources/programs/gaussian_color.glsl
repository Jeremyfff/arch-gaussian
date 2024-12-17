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
uniform sampler2D Tr;// float
uniform sampler2D Tg;// float
uniform sampler2D Tb;// float
uniform sampler2D Ta;// float
in vec2 uv0;

void main() {
    float r = texture(Tr, uv0).x;
    float g = texture(Tg, uv0).x;
    float b = texture(Tb, uv0).x;
    float a = texture(Ta, uv0).x;

    fragColor = vec4(r, g, b, a);

}
#endif
