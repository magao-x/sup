<template>
  <div class="background" :class="[active ? 'active' : '']">
    <video playsinline autoplay muted loop poster="~/assets/flames.jpg">
      <source src="~/assets/flames.mp4" type="video/mp4">
      <source src="~/assets/flames.mp4" type="video/webm">
    </video>
  </div>
</template>
<style lang="scss" scoped>
.background {
  position: fixed;
  z-index: -1;
  width: 100%;
  top: 0;
  left: 0;
  right: 0;
  left: 0;
  height: 100%;
  video {
    object-fit: cover;
    width: 100vw;
    height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    opacity: 0.0;
    transition: opacity 1s;
  }
}
.background.active video {
  opacity: 0.2;
}
</style>
<script>
export default {
  props: ['active']
}
</script>