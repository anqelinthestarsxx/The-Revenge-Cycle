#version 410 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D screenTex;
uniform sampler2D lightTex;
uniform sampler2D tileTex;
uniform sampler2D uiTex;
uniform sampler2D noiseTex;

uniform int menu = 0;

uniform float time;

uniform float scrollX;
uniform float scrollY;
uniform float scrWidth;
uniform float scrHeight;
uniform float levelX;
uniform float levelY;
uniform float levelW;
uniform float levelH;
uniform float levelScale;

uniform vec3 tint = vec3(0.7686, 0.1725, 0.21176);
uniform float tintFactor = 1.0;

void main() {
  vec2 scrUV = TexCoord * vec2(scrWidth, scrHeight);
  vec2 texelSize = vec2(1.0 / scrWidth, 1.0 / scrHeight);
  vec2 levelMin = vec2(levelX, levelY);
  vec2 levelMax = levelMin + vec2(levelW, levelH);
  if (scrUV.x < levelMin.x + texelSize.x ||
      scrUV.y < levelMin.y + texelSize.y ||
      scrUV.x >= levelMax.x - texelSize.x ||
      scrUV.y >= levelMax.y - texelSize.y) {
    FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    return;
  }

  vec4 uiSample = texture(uiTex, TexCoord);

  if (uiSample.r + uiSample.b + uiSample.g > 0.01) {
    FragColor = vec4(uiSample.rgb, 1.0);
    return;
  } else if (menu > 0) {
    float ar = scrWidth / scrHeight;
    vec2 scroll = vec2(scrollX, scrollY);
    vec2 levelOffset = vec2(levelX, levelY);
    scrUV = floor(scrUV / levelScale) * levelScale;
    vec2 levelPos = (scrUV - levelOffset) / levelScale;
    vec2 uv = levelPos * 0.002;
    // uv.y *= 0.5;
    float noise_1 = texture(noiseTex, ar * (uv + vec2(0.0, time * 0.0005))).r;
    float noise_2 = texture(noiseTex, ar * (uv + vec2(0.0, time * 0.00009))).r;
    float noise_3 = texture(noiseTex, ar * (uv + vec2(0.0, time * 0.00004))).r;

    vec2 center = vec2(levelW, levelH) / levelScale * 0.5;
    float levelDist = distance(center, levelPos) / levelW * levelScale;
    float n =
        (noise_1 + noise_2 + noise_3) * 0.3333 * min(1.0, levelDist * 2.0);
    // n = levelDist * 2.0 + n * 0.01;

    vec3 color;
    if (n < 0.3) {
      color = vec3(0.0784, 0.0627, 0.125);
    } else if (n < 0.4) {
      color = vec3(0.208, 0.078, 0.157);
    } else if (n < 0.5) {
      color = vec3(0.0784, 0.0627, 0.125);
    } else {
      color = vec3(0.471, 0.1216, 0.1725);
    }
    // } else {
    // color = vec3(0.769, 0.1725, 0.2118);
    // }

    FragColor = vec4(color, 1.0);
    return;
  }

  vec4 tex = texture(screenTex, TexCoord);
  vec4 tileTex = texture(tileTex, TexCoord);
  float grey = (tex.r + tex.g + tex.b) * 0.33333;

  vec2 scroll = vec2(scrollX, scrollY);
  vec2 levelOffset = vec2(levelX, levelY);
  vec2 levelPos = (scrUV - levelOffset) / levelScale;

  vec2 baseTile = floor(scroll / 16.0) - vec2(1.0);
  vec2 tileWS = (scroll + levelPos) / 16.0;
  vec2 tileLS = tileWS - baseTile;
  vec2 lightSize = vec2(textureSize(lightTex, 0));

  vec2 lightUV = (tileLS + vec2(0.5)) / lightSize;
  vec2 minUV = vec2(0.5) / lightSize;
  vec2 maxUV = (lightSize - vec2(0.5)) / lightSize;
  lightUV = clamp(lightUV, minUV, maxUV);

  vec3 light = vec3(1.0);
  if (grey > 0.0) {
    light = texture(lightTex, lightUV - texelSize * 8.0).rgb;
  }
  if (!(tileTex.r + tileTex.b + tileTex.g > 0.01 ||
        (levelMax.y - scrUV.y) / (levelMax.y - levelMin.y) < 0.1)) {
    light = vec3(1.0);
  }

  vec3 diffuse = mix(tint, tex.rgb * light, tintFactor);
  FragColor = vec4(diffuse, 1.0);
}