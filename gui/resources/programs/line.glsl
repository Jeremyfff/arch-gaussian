#version 420
#include "arch_gaussian.glsl"
#define USE_RGBA 1

#if defined(VERTEX_SHADER)
in vec3 in_position;

void main() {
    gl_Position = GetGLPosition(in_position);
}

#elif defined(FRAGMENT_SHADER)
#if USE_RGBA
uniform vec4 color;
#else
uniform vec3 color;
#endif
out vec4 fragColor;

void main() {
    #if USE_RGBA
        fragColor =color;
    #else
        fragColor=vec4(color, 1.0);
    #endif
}
#endif
