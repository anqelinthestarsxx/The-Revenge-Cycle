#version 410 core

in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D screenTex;
uniform sampler2D lightTex;

uniform float scrollX;
uniform float scrollY;
uniform float scrWidth;
uniform float scrHeight;
uniform float levelX;
uniform float levelY;
uniform float levelScale;

uniform vec3 tint = vec3(1.0);

void main() {
  vec2 texelSize = vec2(1.0 / scrWidth, 1.0 / scrHeight);
  vec4 tex = texture(screenTex, TexCoord);
  float grey = (tex.r + tex.g + tex.b) * 0.33333;

  vec2 scrUV = TexCoord * vec2(scrWidth, scrHeight);
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

  vec3 diffuse = mix(tint, tex.rgb * light, 1.0);
  FragColor = vec4(diffuse, 1.0);
}