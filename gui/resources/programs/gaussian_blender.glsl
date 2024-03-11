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
uniform sampler2D gaussian_color_texture;// vec3
uniform sampler2D gaussian_depth_texture;// float
uniform sampler2D geometry_color_texture;// vec4
uniform sampler2D geometry_depth_texture;// float
in vec2 uv0;

void main() {
    vec4 gaussian_color = texture(gaussian_color_texture, uv0);
    float gaussian_depth = texture(gaussian_depth_texture, uv0).x;
    vec4 geometry_color = texture(geometry_color_texture, uv0);
    float geometry_depth = texture(geometry_depth_texture, uv0).x;

    if (gaussian_depth < geometry_depth){
        // geometry is behind gaussian
        fragColor = gaussian_color;
    }else{
        // geometry if front of gaussian
        vec3 geo_rgb = geometry_color.xyz;
        vec3 gs_rgb = gaussian_color.xyz;
        vec3 mixed_color = geometry_color.a * geo_rgb + (1 - geometry_color.a) * gs_rgb;
        fragColor = vec4(mixed_color, 1.0);
    }
}
#endif
