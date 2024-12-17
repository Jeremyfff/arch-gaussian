#version 330

#define USE_RGBA 1

#if defined(VERTEX_SHADER)

in vec3 in_position;
#if USE_RGBA
in vec4 in_color;
#else
in vec3 in_color;
#endif


uniform mat4 m_model;
uniform mat4 m_camera;
uniform mat4 m_proj;

out vec4 v_color;

void main() {
    mat4 m_view = m_camera * m_model;
    vec4 p = m_view * vec4(in_position, 1.0);
    gl_Position = m_proj * p;

#if USE_RGBA
    v_color = in_color;
#else
    v_color = vec4(in_color, 1.0);
#endif
}

#elif defined(FRAGMENT_SHADER)

in vec4 v_color;
out vec4 fragColor;

void main() {
    fragColor = v_color;
}
#endif
