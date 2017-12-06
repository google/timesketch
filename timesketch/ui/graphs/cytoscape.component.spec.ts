import {Component, ViewChild} from '@angular/core'
import {TestBed, ComponentFixture} from '@angular/core/testing'
import {BrowserDynamicTestingModule, platformBrowserDynamicTesting} from '@angular/platform-browser-dynamic/testing'
import {BrowserModule} from '@angular/platform-browser'

import {CytoscapeComponent} from './cytoscape.component'

export const testCytoscapeOptions = Object.seal({
  zoomingEnabled: false,
  userZoomingEnabled: false,
  panningEnabled: false,
  userPanningEnabled: false,
  boxSelectionEnabled: true,
  autolock: true,
  autoungrabify: true,
  autounselectify: true,
  headless: true,
  hideEdgesOnViewport: true,
  hideLabelsOnViewport: true,
  textureOnViewport: true,
  motionBlur: true,
  styleEnabled: false,
  minZoom: 1e-10,
  maxZoom: 1e10,
  touchTapThreshold: 10,
  desktopTapThreshold: 6,
  motionBlurOpacity: 0.4,
  wheelSensitivity: 0.8,
  pixelRatio: 1.0,
  selectionType: 'additive',
})

export function getOptionFromCytoscape(_cy: Cy.Core, option: string): any {
  type CytoscapeInternals = {
    [option in keyof Cy.CytoscapeOptions]?: () => {}
  } & {json: () => {}} & {_private: {
    options: {[option in keyof Cy.CytoscapeOptions]?: {}},
    renderer: {options: {[option in keyof Cy.CytoscapeOptions]?: {}}},
  }}
  const cy: CytoscapeInternals = _cy as any
  if (option in cy) {
    return cy[option]()
  } else if (option in cy.json()) {
    return cy.json()[option]
  } else {
    return cy._private.options[option] || cy._private.renderer.options[option]
  }
}

export const testCytoscapeEvents = [
  'mousedown', 'mouseup', 'click', 'mouseover', 'mouseout', 'mousemove',
  'touchstart', 'touchmove', 'touchend', 'tapstart', 'vmousedown',
  'tapdrag', 'vmousemove', 'tapdragover', 'tapdragout', 'tapend',
  'vmouseup', 'tap', 'vclick', 'taphold', 'cxttapstart', 'cxttapend',
  'cxttap', 'cxtdrag', 'cxtdragover', 'cxtdragout', 'boxstart', 'boxend',
  'boxselect', 'box', 'layoutstart', 'layoutready', 'layoutstop',
  'destroy', 'render', 'resize',
]

describe('CytoscapeComponent', () => {
  beforeAll(() => {
    TestBed.resetTestEnvironment()
    TestBed.initTestEnvironment(
      BrowserDynamicTestingModule, platformBrowserDynamicTesting(),
    )
  })

  describe('options', () => {
    let fixture: ComponentFixture<OptionsTestComponent>
    beforeEach(async () => {
      TestBed.configureTestingModule({
        imports: [BrowserModule],
        declarations: [CytoscapeComponent, OptionsTestComponent],
      })
      fixture = TestBed.createComponent(OptionsTestComponent)
      // prevent 'Error: Timeout - Async callback was not invoked within timeout':
      fixture.componentInstance.cytoscapeComponent['cytoscapeHostRef'] = undefined
      await fixture.whenStable()
    })

    for (const [option, value] of Object.entries(testCytoscapeOptions)) {
      it(`should handle changes of "${option}" correctly`, () => {
        fixture.detectChanges()
        fixture.componentInstance.options[option] = value
        fixture.detectChanges()
        const cy = fixture.componentInstance.cytoscapeComponent.cy
        const newValue = getOptionFromCytoscape(cy, option)
        expect(newValue).toEqual(value)
      })
    }

    for (const option_to_change of Object.keys(testCytoscapeOptions)) {
      it(`should retain other options after changing "${option_to_change}"`, () => {
        fixture.componentInstance.options = {...testCytoscapeOptions}
        fixture.detectChanges()
        if (option_to_change === 'styleEnabled') {
          fixture.componentInstance.options[option_to_change] = 'true'
        }
        if (testCytoscapeOptions[option_to_change] === 'additive') {
          fixture.componentInstance.options[option_to_change] = 'single'
        }
        if (typeof testCytoscapeOptions[option_to_change] === 'boolean') {
          fixture.componentInstance.options[option_to_change] = !fixture.componentInstance.options[option_to_change]
        }
        if (typeof testCytoscapeOptions[option_to_change] === 'number') {
          fixture.componentInstance.options[option_to_change] = 3.1415
        }
        fixture.detectChanges()
        const cy = fixture.componentInstance.cytoscapeComponent.cy
        for (const [option, value] of Object.entries(testCytoscapeOptions)) {
          if (option !== option_to_change) {
            const actualValue = getOptionFromCytoscape(cy, option)
            expect(actualValue).toEqual(value)
          }
        }
      })
    }
  })

  describe('events', () => {
    let fixture: ComponentFixture<EventsTestComponent>
    beforeEach(async () => {
      TestBed.configureTestingModule({
        imports: [BrowserModule],
        declarations: [CytoscapeComponent, EventsTestComponent],
      })
      fixture = TestBed.createComponent(EventsTestComponent)
      // prevent 'Error: Timeout - Async callback was not invoked within timeout':
      fixture.componentInstance.cytoscapeComponent['cytoscapeHostRef'] = undefined
      fixture.detectChanges()
      await fixture.whenStable()
      fixture.detectChanges()
      fixture.componentInstance.events = []
    })

    for (const event_name of testCytoscapeEvents) {
      it(`should correctly emit "${event_name}"`, () => {
        const cy = fixture.componentInstance.cytoscapeComponent.cy
        cy.emit(event_name)
        const [[recorded_event, recorded_name]] = fixture.componentInstance.events
        expect(recorded_name).toEqual(event_name)
        expect(recorded_event.type).toEqual(event_name)
      })
    }

    for (const event_name of testCytoscapeEvents) {
      it(`should correctly emit "${event_name}", even after re-initialization`, () => {
        // change some immutable option to force re-initialization of cytoscape
        fixture.componentInstance.options['motionBlur'] = true
        fixture.detectChanges()
        const cy = fixture.componentInstance.cytoscapeComponent.cy
        fixture.componentInstance.events = []
        cy.emit(event_name)
        const [[recorded_event, recorded_name]] = fixture.componentInstance.events
        expect(recorded_name).toEqual(event_name)
        expect(recorded_event.type).toEqual(event_name)
      })
    }

    it(`should correctly emit "panChange"`, () => {
      const cy = fixture.componentInstance.cytoscapeComponent.cy
      cy.pan({x: 1, y: 2})
      const options = fixture.componentInstance.options
      expect(options['pan'].x).toEqual(1)
      expect(options['pan'].y).toEqual(2)
    })

    it(`should correctly emit "zoomChange"`, () => {
      const cy = fixture.componentInstance.cytoscapeComponent.cy
      cy.zoom(2)
      const options = fixture.componentInstance.options
      expect(options['zoom']).toEqual(2)
    })

  })
})

// tslint:disable:max-classes-per-file

@Component({
  template: `
    <ts-graphs-cytoscape
      [elements]="options.elements"
      [style]="options.style"
      [layout]="options.layout"

      [(zoom)]="options.zoom"
      [(pan)]="options.pan"

      [minZoom]="options.minZoom"
      [maxZoom]="options.maxZoom"
      [zoomingEnabled]="options.zoomingEnabled"
      [userZoomingEnabled]="options.userZoomingEnabled"
      [panningEnabled]="options.panningEnabled"
      [userPanningEnabled]="options.userPanningEnabled"
      [boxSelectionEnabled]="options.boxSelectionEnabled"
      [selectionType]="options.selectionType"
      [touchTapThreshold]="options.touchTapThreshold"
      [desktopTapThreshold]="options.desktopTapThreshold"
      [autolock]="options.autolock"
      [autoungrabify]="options.autoungrabify"
      [autounselectify]="options.autounselectify"

      [headless]="options.headless"
      [styleEnabled]="options.styleEnabled"
      [hideEdgesOnViewport]="options.hideEdgesOnViewport"
      [hideLabelsOnViewport]="options.hideLabelsOnViewport"
      [textureOnViewport]="options.textureOnViewport"
      [motionBlur]="options.motionBlur"
      [motionBlurOpacity]="options.motionBlurOpacity"
      [wheelSensitivity]="options.wheelSensitivity"
      [pixelRatio]="options.pixelRatio"
    ></ts-graphs-cytoscape>
  `,
})
class OptionsTestComponent {
  @ViewChild(CytoscapeComponent) cytoscapeComponent: CytoscapeComponent
  options = {}
}

@Component({
  template: `
    <ts-graphs-cytoscape
      [(zoom)]="options.zoom"
      [(pan)]="options.pan"

      [motionBlur]="options.motionBlur"

      (mousedown)="handle($event, 'mousedown')"
      (mouseup)="handle($event, 'mouseup')"
      (click)="handle($event, 'click')"
      (mouseover)="handle($event, 'mouseover')"
      (mouseout)="handle($event, 'mouseout')"
      (mousemove)="handle($event, 'mousemove')"
      (touchstart)="handle($event, 'touchstart')"
      (touchmove)="handle($event, 'touchmove')"
      (touchend)="handle($event, 'touchend')"
      (tapstart)="handle($event, 'tapstart')"
      (vmousedown)="handle($event, 'vmousedown')"
      (tapdrag)="handle($event, 'tapdrag')"
      (vmousemove)="handle($event, 'vmousemove')"
      (tapdragover)="handle($event, 'tapdragover')"
      (tapdragout)="handle($event, 'tapdragout')"
      (tapend)="handle($event, 'tapend')"
      (vmouseup)="handle($event, 'vmouseup')"
      (tap)="handle($event, 'tap')"
      (vclick)="handle($event, 'vclick')"
      (taphold)="handle($event, 'taphold')"
      (cxttapstart)="handle($event, 'cxttapstart')"
      (cxttapend)="handle($event, 'cxttapend')"
      (cxttap)="handle($event, 'cxttap')"
      (cxtdrag)="handle($event, 'cxtdrag')"
      (cxtdragover)="handle($event, 'cxtdragover')"
      (cxtdragout)="handle($event, 'cxtdragout')"
      (boxstart)="handle($event, 'boxstart')"
      (boxend)="handle($event, 'boxend')"
      (boxselect)="handle($event, 'boxselect')"
      (box)="handle($event, 'box')"
      (layoutstart)="handle($event, 'layoutstart')"
      (layoutready)="handle($event, 'layoutready')"
      (layoutstop)="handle($event, 'layoutstop')"
      (ready)="handle($event, 'ready')"
      (destroy)="handle($event, 'destroy')"
      (render)="handle($event, 'render')"
      (resize)="handle($event, 'resize')"
    ></ts-graphs-cytoscape>
  `,
})
class EventsTestComponent {
  @ViewChild(CytoscapeComponent) cytoscapeComponent: CytoscapeComponent
  options = {}
  events = []
  handle(event, name) {
    this.events.push([event, name])
  }
}
