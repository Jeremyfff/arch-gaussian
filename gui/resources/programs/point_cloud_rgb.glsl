#version 330

#if defined VERTEX_SHADER

in vec3 in_position;
in vec3 in_color;

uniform mat4 m_model;
uniform mat4 m_camera;
uniform mat4 m_proj;

out vec3 v_color;

void main() {
    mat4 m_view = m_camera * m_model;
    vec4 p = m_view * vec4(in_position.x, in_position.y, in_position.z, 1.0);
    gl_Position = m_proj * p;
    v_color = in_color;
}

#elif defined FRAGMENT_SHADER

in vec3 v_color;
out vec4 fragColor;

void main() {
    fragColor =vec4(v_color, 1.0);
}
#endif
