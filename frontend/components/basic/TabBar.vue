<template>
  <div v-if="invalidLayout" class="error">Configuration <code>layout</code> value <code>{{ $store.state.config.layout }}</code> is invalid. Please update the config file.</div>
  <nav v-else class="top">
    <div id="logo">
      <img @click="toggleFlames" src="~/assets/magao-x_logo_white.svg">
    </div>
    <div class="tab-bar">
      <router-link v-for="(tab, key) of tabs" :to="tabs[key].path" class="tab btn" :class="key">
        <span class="nav-icon">
          <i class="material-icons">{{ tabs[key].icon }}</i>
        </span>
        <span class="label">{{ tabs[key].label }}</span>
      </router-link>
    </div>
  </nav>
</template>
<style lang="scss" scoped>
@use "~/css/variables.scss" as *;
.error {
  padding: 1em;
  color: $error;
  font-weight: bold;
  font-size: 18px;
  text-align: center;
}

#logo {
  height: 100%;
  
  flex: 1;
  position: relative;
  text-align: right;
  // padding-top: 1.5rem;
  vertical-align: middle;
  img {
   box-sizing: border-box;
    // padding: 0 1rem;
    width: 168px;
    filter: drop-shadow(0px 0px 5px #3daee9);
    mix-blend-mode: screen;
    // position: absolute;
    // right: 0;
    // margin-bottom: -25px;
    // display: block;
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
  padding: 1.5rem 1rem 0rem 1rem;
  margin: 0;
  .tab {
    // background: var(--bg-normal);
    display: block;
    padding: calc($unit / 2);
    border-top: 1px solid var(--border);
    border-right: 1px solid var(--border);
    border-bottom: none;
    text-decoration: none;
    &:first-child {
      border-left: 1px solid var(--border);
    }
    .label {
      text-decoration: underline;
    }
    &:hover, &.router-link-exact-active {
      color: var(--fg-normal);
      background: $plasma-blue;
      border-top: 1px solid $plasma-blue;
      border-right: 1px solid $plasma-blue;
      border-left: 1px solid $plasma-blue;
    }
  }
}
</style>
<script>
import { map } from '~/map.js'

export default {
  inject: ['toggleFlames'],
  computed: {
    invalidLayout() {
      const layout = this.$store.state.config.layout;
      return !(map[layout] && map[layout]['tabs']);
    },
    tabs() {
      if (this.invalidLayout) {
        return {};
      }
      const layout = this.$store.state.config.layout;
      return map[layout].tabs;
    },
  },
};
</script>