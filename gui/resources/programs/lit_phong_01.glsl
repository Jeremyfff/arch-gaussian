#version 420
#include "arch_gaussian.glsl"
#if defined(VERTEX_SHADER)
in vec3 in_position;
in vec3 in_normal;
in vec2 in_texcoord_0;

out vec3 posOS;
out vec3 posWS;
out vec3 normalOS;
out vec3 normalWS;
out vec3 shadowCoord;

out vec2 uv;


void main() {
    gl_Position = GetGLPosition(in_position);

    posOS = in_position;
    posWS = PositionObjectToWorld(posOS);

    normalOS = in_normal;
    normalWS = NormalObjectToWorld(normalOS);

    shadowCoord = GetShadowCoord(posOS);

    uv = in_texcoord_0;
}

#elif defined(FRAGMENT_SHADER)

in vec3 posOS;
in vec3 posWS;
in vec3 normalOS;
in vec3 normalWS;
in vec3 shadowCoord;
in vec2 uv;

out vec4 fragColor;

uniform vec4 _Color;

uniform sampler2D _ShadowMap;
uniform float _Bias;
uniform float _PoissonDistRadiusDiv;
vec2 poissonDisk[4] = vec2[](
vec2(-0.94201624, -0.39906216),
vec2(0.94558609, -0.76890725),
vec2(-0.094184101, -0.92938870),
vec2(0.34495938, 0.29387760)
);

void main() {
    float visibility = 1.0;
    float d = 0.5 / 4.0;
    for (int i = 0; i < 4; i++) {
        if (texture(_ShadowMap, shadowCoord.xy + poissonDisk[i] / _PoissonDistRadiusDiv).r < shadowCoord.z - _Bias) {
            visibility -= d;
        }
    }
    // Phong Lighing
    // https://learnopengl-cn.github.io/02%20Lighting/02%20Basic%20Lighting/

    vec3 lightColor = light_data.light_color;
    vec3 lightDir = normalize(-light_data.light_dir);

    // ambient
    float ambientStrength = 0.2;
    vec3 ambient = ambientStrength * lightColor;
    // diffuse
    float diffuseStrength = 0.5;

    float diff = max(dot(lightDir, normalWS), 0.0);
    vec3 diffuse = diffuseStrength * diff * lightColor * visibility;

    // specular
    float specularStrength = 1;
    vec3 viewDir = normalize(common_data.view_pos - posWS);
    vec3 reflectDir = reflect(-lightDir, normalWS);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
    vec3 specular = specularStrength * spec * lightColor;

    vec3 result = (ambient + diffuse + specular) * _Color.rgb;

    fragColor.rgb = clamp(result, 0, 1);
//    fragColor.rgb = fragColor.rgb * 0.1 + common_data.view_pos * 0.9;
    fragColor.a = 1.0;

}
#endif
