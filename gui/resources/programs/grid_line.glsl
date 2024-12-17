#version 420
#include "arch_gaussian.glsl"

#if defined(VERTEX_SHADER)

in vec3 in_position;

out vec3 posWS;

void main() {
    gl_Position = GetGLPosition(in_position);
    posWS = PositionObjectToWorld(in_position);
}

#elif defined(FRAGMENT_SHADER)

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
