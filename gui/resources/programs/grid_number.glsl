#version 330

#if defined VERTEX_SHADER

in vec3 in_position;

uniform mat4 m_model;
uniform mat4 m_camera;
uniform mat4 m_proj;

out vec3 posWS;

void main() {
    mat4 m_view = m_camera * m_model;
    vec4 in_position4 = vec4(in_position.x, in_position.y, in_position.z, 1.0);
    vec4 p = m_view * in_position4;
    gl_Position = m_proj * p;

    posWS = (m_model * in_position4).xyz;
}

#elif defined FRAGMENT_SHADER

in vec3 posWS;

uniform vec4 color;
uniform vec3 camPosWS;
uniform float maxDist;

out vec4 fragColor;

void main() {
    float distanceToCamera = distance(camPosWS, posWS);

    float brightness = 1 - clamp(distanceToCamera / maxDist, 0.0, 1.0);
    brightness = pow(brightness, 2);
    fragColor = vec4(color.r, color.g, color.b, color.a * brightness);
}
#endif
