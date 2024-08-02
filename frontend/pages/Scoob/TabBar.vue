<template>
  <nav class="top">
    <div id="logo">
      <img @click="toggleFlames" src="~/assets/magao-x_logo_white.svg">
    </div>
    <div class="tab-bar">
      <router-link to="/" class="tab btn observation">
        <span class="nav-icon">
          <i class="material-icons">visibility</i>
        </span>
        <span class="label">observation</span>
      </router-link>
      <router-link to="/cameras" class="tab btn cameras">
        <span class="nav-icon">
          <i class="material-icons">camera</i>
        </span>
        <span class="label">cameras</span>
      </router-link>
      <router-link to="/power" class="tab btn power">
        <span class="nav-icon">
          <i class="material-icons">power_settings_new</i>
        </span>
        <span class="label">power</span>
      </router-link>
    </div>
  </nav>
</template>
<style lang="scss" scoped>
@import "./css/variables.scss";

#logo {
  height: 100%;
  display: flex;
flex: 1;
position: relative;
 img {
    width: 168px;
    padding: 0 1rem;
    filter: drop-shadow(0px 0px 5px #3daee9);
    mix-blend-mode: screen;
    position: absolute;
    right: 0;
    top: 0.5rem;
  }
}

nav.top {
  position: relative;
  // padding-right: 15vw;
  background-color: var(--inset-bg);
  border-bottom: 3px solid $plasma-blue;
  display: flex;
  flex-flow: row-reverse wrap;
}


nav.top .tab-bar {
  display: flex;
  padding: 1rem 1rem 0rem 1rem;
  margin: 0;
  .tab {
    // background: var(--bg-normal);
    display: block;
    padding: calc($unit / 2);
    border-top: 1px solid var(--border);
    border-right: 1px solid var(--border);
    border-bottom: none;
    &:first-child {
      border-left: 1px solid var(--border);
    }
    text-decoration: none;
    .label {
      text-decoration: underline;
    }
    &:hover, &.router-link-exact-active {
      color: var(--fg-normal);
      background: $plasma-blue;
      border-top: 1px solid $plasma-blue;
      border-right: 1px solid $plasma-blue;
      // &:first-child {
        border-left: 1px solid $plasma-blue;
      // }
    }
  }
}
</style>
<script>
export default {
  inject: ['toggleFlames']
};
</script>