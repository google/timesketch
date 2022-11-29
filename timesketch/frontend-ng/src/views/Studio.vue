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
    <div>
        <!-- Left panel -->
        <v-navigation-drawer app permanent :width="navigationDrawer.width"
            hide-overlay ref="drawer">
            <v-toolbar flat>
                <v-avatar class="mt-2 ml-n4">
                    <router-link to="/">
                        <v-img src="/dist/timesketch-color.png" max-height="25"
                            max-width="25" contain></v-img>
                    </router-link>
                </v-avatar><b>Studio</b>
                <v-spacer></v-spacer>
                <v-icon @click="hideDrawer()">mdi-chevron-left</v-icon>
            </v-toolbar>
            <v-divider></v-divider>

            <ts-scenario :scenario="scenario"></ts-scenario>
            <br />
            <ts-data-types></ts-data-types>
            <ts-tags></ts-tags>
            <ts-search-templates></ts-search-templates>
            <ts-sigma-rules></ts-sigma-rules>
        </v-navigation-drawer>
        {{ type }}
        <ts-sigma-rule-modification app @cancel="formatXMLString = false"
            :rule_uuid="id" v-if="type === 'sigma'">
        </ts-sigma-rule-modification>
        <ts-search-template-modification app :id="id"
            v-if="type === 'searchtemplate'">
        </ts-search-template-modification>

    </div>

</template>
  
<script>
import TsScenario from '../components/Scenarios/Scenario'
import TsDataTypes from '../components/LeftPanel/DataTypes'
import TsTags from '../components/LeftPanel/Tags'
import TsSearchTemplates from '../components/LeftPanel/SearchTemplates'
import TsSigmaRules from '../components/LeftPanel/SigmaRules'
import TsSigmaRuleModification from '../components/Studio/SigmaRuleModification.vue'
import TsSearchTemplateModification from '../components/Studio/SearchTemplateModification.vue'

export default {
    props: ['showLeftPanel', 'id', 'type'],
    components: {
        TsScenario,
        TsDataTypes,
        TsTags,
        TsSearchTemplates,
        TsSigmaRules,
        TsSigmaRuleModification,
        TsSearchTemplateModification,
    },
    data() {
        return {
            showSketchMetadata: false,
            navigationDrawer: {
                width: 450,
            },
            sketchId: 1, // TODO: this must be removed
        }
    },
    created: function () {
        this.$store.dispatch('updateSketch', this.sketchId)
        this.$store.dispatch('updateSearchHistory', this.sketchId)
        this.$store.dispatch('updateScenario', this.sketchId)
        this.$store.dispatch('updateSigmaList')
        document.title = 'Timesketch Studio'
    },
    updated() {
        this.$nextTick(function () {
            this.setDrawerBorderStyle()
            this.setDrawerResizeEvents()
        })
    },
    computed: {
        meta() {
            return this.$store.state.meta
        },
        scenario() {
            return this.$store.state.scenario
        },

    },
    methods: {
        hideDrawer() {
            this.navigationDrawer.width = 0
            this.$emit('hideLeftPanel')
        },
        setDrawerBorderStyle() {
            let i = this.$refs.drawer.$el.querySelector('.v-navigation-drawer__border')
            i.style.cursor = 'ew-resize'
        },
        setDrawerResizeEvents() {
            const minSize = 1
            const drawerElement = this.$refs.drawer.$el
            const drawerBorder = drawerElement.querySelector('.v-navigation-drawer__border')
            const direction = drawerElement.classList.contains('v-navigation-drawer--right') ? 'right' : 'left'
            function resize(e) {
                document.body.style.cursor = 'ew-resize'
                let f = direction === 'right' ? document.body.scrollWidth - e.clientX : e.clientX
                drawerElement.style.width = f + 'px'
            }
            drawerBorder.addEventListener(
                'mousedown',
                (e) => {
                    if (e.offsetX < minSize) {
                        drawerElement.style.transition = 'initial'
                        document.addEventListener('mousemove', resize, false)
                    }
                },
                false
            )
            document.addEventListener(
                'mouseup',
                () => {
                    drawerElement.style.transition = ''
                    this.navigationDrawer.width = drawerElement.style.width
                    document.body.style.cursor = ''
                    document.removeEventListener('mousemove', resize, false)
                },
                false
            )
        },
    },
    watch: {
        showLeftPanel: function (newVal) {
            if (newVal === true) {
                this.navigationDrawer.width = 450
            }
        },
    },
}
</script>
  