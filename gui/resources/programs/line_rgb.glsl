#version 330

#if defined VERTEX_SHADER

in vec3 in_position;

uniform mat4 m_model;
uniform mat4 m_camera;
uniform mat4 m_proj;


void main() {
    mat4 m_view = m_camera * m_model;
    vec4 p = m_view * vec4(in_position.x, in_position.y, in_position.z, 1.0);
    gl_Position = m_proj * p;
}

#elif defined FRAGMENT_SHADER

uniform vec3 color;
out vec4 fragColor;

void main() {
    fragColor =vec4(color, 1.0);
}
#endif
