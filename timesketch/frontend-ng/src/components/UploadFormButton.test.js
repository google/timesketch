/*
Copyright 2024 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

import {mount} from "@vue/test-utils"
import UploadFormButton from './UploadFormButton.vue'
import Vuetify from 'vuetify'
import Vue from "vue"
import { expect } from "chai"
import { vi } from "vitest"

let vuetify
let wrapper
let uploadFormStub
let uploadFormSlotProps

Vue.use(Vuetify)

beforeEach(() => {
  vuetify = new Vuetify()
  uploadFormSlotProps = {
    on: {click: vi.fn()},
    attrs: [],
  }

  uploadFormStub = {
    name: 'UploadFormStub',
    template: `
      <span>
          <slot :on="on" :attrs="attrs"></slot>
      </span>
    `,
    data() {
      return uploadFormSlotProps
    }
  }

  wrapper = mount(UploadFormButton, {
    vuetify,
    stubs: {'ts-upload-timeline-form': uploadFormStub},
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

it("contains text", async () => {
  expect(wrapper.text()).toContain('Add Timeline')
});

it("renders a large button by default", () => {
  const button = wrapper.findComponent({ name: 'v-btn' })
  const icon = button.findComponent({ name: 'v-icon' })
  const buttonProps = button.props()
  const iconProps = icon.props()

  expect(buttonProps.small).toBe(false)
  expect(buttonProps.text).toBe(false)
  expect(buttonProps.rounded).toBe(true)
  expect(buttonProps.depressed).toBe(true)
  expect(iconProps.small).toBe(false);
});

it("renders a small button", async () => {
  await wrapper.setProps({btnType: 'small'})
  const button = wrapper.findComponent({ name: 'v-btn' })
  const icon = button.findComponent({ name: 'v-icon' })
  const buttonProps = button.props()
  const iconProps = icon.props()

  expect(buttonProps.small).toBe(true)
  expect(buttonProps.text).toBe(true)
  expect(buttonProps.rounded).toBe(true)
  expect(buttonProps.depressed).toBe(false)
  expect(iconProps.small).toBe(true);
});

it("delegates click", async () => {
  const button = wrapper.findComponent({ name: 'v-btn' })
  expect(uploadFormSlotProps.on.click).toHaveBeenCalledTimes(0)

  await button.trigger('click')

  expect(uploadFormSlotProps.on.click).toHaveBeenCalledTimes(1)
});
