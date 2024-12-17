
layout (std140, binding = 1) uniform CommonData {
    float time;
    mat4 m_world;
    vec3 view_pos;
} common_data;

layout (std140, binding = 2) uniform CameraData {
    mat4 m_camera;
    mat4 m_proj;
    vec3 view_pos;
} camera_data;

layout (std140, binding = 3) uniform LightData {
    mat4 m_depth; // m_depth = m_bias * m_proj * m_camera, (world space) -> (view space) -> (clip space) -> (tex space)
    vec3 light_dir; // World Space
    vec3 light_color;

} light_data;

uniform mat4 m_model;