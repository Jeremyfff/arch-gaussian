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
in vec2 uv0;

uniform float iTime;
uniform vec2  iResolution;

uniform vec4 _BgColor;
uniform float _BandSpacing;    //value=.5, min=0, max=1, step=0.01
uniform float _FrequencyY;    //value=2., min=0.1, max=4, step=0.01
uniform float _SpeedZ;    //value=4., min=0., max=32, step=0.01
uniform float _RandomSpeed;    //value=3., min=0., max=8, step=0.01
uniform float _FrequencyZ;    //value=.03, min=0.001, max=0.1, step=0.01


vec3 hash31(float p)
{
   vec3 p3 = fract(p * vec3(.1031, .1030, .0973));
   p3 += dot(p3, p3.yzx+19.19);
   return fract((p3.xxy+p3.yzz)*p3.zyx);
}

vec3 spectrum(in float d)
{
    return smoothstep(0.25, 0., abs(d + vec3(0.125,0.,-0.125)));
}

void main() {
    // https://oneshader.net/shader/ffb37ed776
    vec3 color = vec3(.0);
    float z = iTime * _SpeedZ;

    float zOffset = z * _RandomSpeed;
    vec2 uv = gl_FragCoord.xy/iResolution - 0.5;
    uv.x *= iResolution.x / iResolution.y;

    vec3 ray = normalize(vec3(uv, 1.5));
    float l = length(ray.xy);
    float r = 1.;
    for(int i = 0; i < 4; i++){
        vec3 hit = (ray / abs(ray.x)) * r++;
        vec3 p = hit;
        p.z += z;

        float seed = p.x * 7. + p.y + 5.;

        //give bands uneven width
        p.y += sin(seed * 5.) * _BandSpacing;
        seed = (p.x + p.y) * _FrequencyY;

        vec3 rand = hash31(floor(seed));

        //z animation
        p.z += (rand.x - 0.5) *-zOffset;

        //frequency in z
        p.z *=	_FrequencyZ / (rand.y + 0.05);

        vec2 cell = fract(vec2(seed, p.z)) - 0.5;

        float b = rand.y;
        b *= smoothstep(0.5, 0., abs(cell.x));
        b *= smoothstep(50., 10., length(hit));
        b *= smoothstep(5., 2., abs(hit.y));
        color += spectrum(cell.y) * b;
    }

    color = sqrt(color);
    color *= 1.3 - dot(uv, uv);
    color.r *= 0.2;
    color.g *= 0.5;
    color = _BgColor.rgb + color;
    color = clamp(color, 0.0, 1.0);

    fragColor = vec4(color,1.0);
}
#endif
