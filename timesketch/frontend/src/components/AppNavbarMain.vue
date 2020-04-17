<!--
Copyright 2019 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <nav class="navbar" role="navigation" aria-label="main navigation">
    <div class="navbar-brand">
      <router-link class="navbar-item" to="/">
        <div class="logo" style="margin-top:7px;">
          <img src="/dist/timesketch-white.png">
        </div>
        <span style="color: #fff; margin-left: 7px; margin-top: 1px; font-size: 1.2em;">time<b>sketch</b></span>
      </router-link>
    </div>
    <div class="navbar-end">
      <div class="navbar-item" style="color: #ffffff;">
        {{ currentUser }}
      </div>
      <div class="navbar-item">
        <a href="/logout" style="color:#fff;">Logout</a>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'ts-navbar-main',
  computed: {
    currentUser () {
      return this.$store.state.currentUser
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
  .navbar {
      background: #0070bd;
      padding-left: 32px;
      padding-right: 32px;
  }

  .navbar-item {
      padding-left: 0;
  }

  .logo img {
      width: 15px;
      height: 17px;
  }
</style>
