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
uniform sampler2D pressure_texture;
uniform sampler2D wall_texture;
in vec2 uv0;

void main() {
    float pressure = texture(pressure_texture, uv0).r;
    float wall = texture(wall_texture, uv0).r;
    fragColor = vec4(wall, .1 * pressure, (pressure + 1.0) * 0.5, 1.0) / 2;
    fragColor = vec4(wall, .6549 * pressure, (pressure + 1.0) * 0.5, 1.0);
}
#endif
