

<template>
  <v-menu offset-y :disabled="!isWildcardSupported">
    <template v-slot:activator="{ on, attrs }">
      <v-btn
        depressed
        :color="$vuetify.theme.dark ? 'grey darken-3' : 'grey lighten-3'"
        v-bind="attrs"
        v-on="on"
        height="54"
        min-width="0"
        class="px-2 rounded-0 grey--text"
        :class="$vuetify.theme.dark ? 'text--lighten-3' : 'text--darken-3'"
        :title="!isWildcardSupported ? 'This sketch does not support wildcard searches' : selectedTitle"
        :style="!isWildcardSupported ? 'cursor: default; opacity: 0.8;' : ''"
      >
        {{ selectedValue }}

        <v-icon v-if="isWildcardSupported" small class="ml-1">
          mdi-chevron-down
        </v-icon>
      </v-btn>
    </template>

    <v-list>
      <v-list-item
        v-for="item in menuItems"
        :key="item.value"
        @click="selectItem(item)"
      >
        <v-list-item-title>{{ item.title }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      default: 'QS'
    }
  },
  data() {
    return {
      menuItems: [
        { title: 'Query String', value: 'QS' },
        { title: 'Wildcard', value: 'WC' }
      ],
      selectedValue: this.value,
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta || {};
    },
    isWildcardSupported() {
      return !!this.meta.supports_wildcard;
    },
    selectedTitle() {
      const item = this.menuItems.find(i => i.value === this.selectedValue)
      return item ? item.title : ''
    }
  },
  watch: {
    value(newVal) {
      this.selectedValue = newVal;
    },
    isWildcardSupported: {
      immediate: true,
      handler(supported) {
        if (!supported && this.selectedValue !== 'QS') {
          this.selectedValue = 'QS';
          this.$emit('input', 'QS');
        }
      }
    }
  },
  methods: {
    selectItem(item) {
      this.selectedValue = item.value;
      this.$emit('input', item.value);
    }
  }
}
</script>

<style scoped lang="scss">
</style>
