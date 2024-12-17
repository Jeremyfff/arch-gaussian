#include "uniform_blocks.glsl"

#define PROJ_MATRIX camera_data.m_proj
#define CAMERA_MATRIX camera_data.m_camera
#define LOCAL_TO_WORLD_MATRIX m_model
#define WORLD_MATRIX common_data.m_world

vec3 PositionObjectToWorld(vec3 localPosition) {
    return (LOCAL_TO_WORLD_MATRIX * vec4(localPosition, 1.0)).xyz;
}
vec3 NormalObjectToWorld(vec3 localNormal) {
    return normalize(mat3(transpose(inverse(LOCAL_TO_WORLD_MATRIX))) * localNormal);
}

vec4 GetGLPosition(vec3 in_position) {
    vec4 result = PROJ_MATRIX * CAMERA_MATRIX * WORLD_MATRIX * LOCAL_TO_WORLD_MATRIX * vec4(in_position, 1.0);
    return result;
}

vec3 GetShadowCoord(vec3 localPosition) {
    return (light_data.m_depth * LOCAL_TO_WORLD_MATRIX * vec4(localPosition, 1.0)).xyz;
}