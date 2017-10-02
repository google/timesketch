import {Component, ViewChild} from '@angular/core'
import {TestBed, ComponentFixture} from '@angular/core/testing'
import {BrowserDynamicTestingModule, platformBrowserDynamicTesting} from '@angular/platform-browser-dynamic/testing'
import {BrowserModule, By} from '@angular/platform-browser'
import {FormsModule} from '@angular/forms'

import {CytoscapeComponent} from './cytoscape.component'
import {testCytoscapeOptions, getOptionFromCytoscape} from './cytoscape.component.spec'
import {CytoscapeSettingsComponent} from './cytoscape-settings.component'

describe('CytoscapeComponent', () => {
  beforeAll(() => {
    TestBed.resetTestEnvironment()
    TestBed.initTestEnvironment(
      BrowserDynamicTestingModule, platformBrowserDynamicTesting(),
    )
  })

  const remainingOptions = {...testCytoscapeOptions}

  let fixture: ComponentFixture<SettingsTestComponent>
  beforeEach(async () => {
    TestBed.configureTestingModule({
      imports: [BrowserModule, FormsModule],
      declarations: [CytoscapeComponent, CytoscapeSettingsComponent, SettingsTestComponent],
    })
    fixture = TestBed.createComponent(SettingsTestComponent)
    // prevent 'Error: Timeout - Async callback was not invoked within timeout':
    fixture.componentInstance.cytoscapeComponent['cytoscapeHostRef'] = undefined
    fixture.detectChanges()
    await fixture.whenStable()
  })

  describe('checkboxes', () => {
    it('should work correctly', () => {
      for (const checkboxDebugElement of fixture.debugElement.queryAll(By.css('input[type="checkbox"]'))) {
        const checkbox: HTMLInputElement = checkboxDebugElement.nativeElement
        const label: HTMLElement = checkbox.parentElement
        const labelText = label.textContent.trim()

        expect(labelText in remainingOptions).toBeTruthy()
        delete remainingOptions[labelText]

        if (labelText === 'headless' || labelText === 'styleEnabled') {
          // these cause PhantomJS to hang
          continue
        }
        label.click()
        fixture.detectChanges()

        const cy = fixture.componentInstance.cytoscapeComponent.cy
        expect(Boolean(getOptionFromCytoscape(cy, labelText))).toEqual(!testCytoscapeOptions[labelText])
      }
    })
  })

  describe('number inputs', () => {
    it('should work correctly', () => {
      for (const inputDebugElement of fixture.debugElement.queryAll(By.css('input[type="number"]'))) {
        const input: HTMLInputElement = inputDebugElement.nativeElement
        const label: HTMLElement = input.parentElement
        const labelText = label.textContent.trim()
        const value = testCytoscapeOptions[labelText]

        expect(labelText in remainingOptions).toBeTruthy()
        delete remainingOptions[labelText]

        input.value = String(value + 3)
        input.dispatchEvent(new Event('input'))
        fixture.detectChanges()

        const cy = fixture.componentInstance.cytoscapeComponent.cy
        expect(getOptionFromCytoscape(cy, labelText)).toEqual(value + 3)
      }
    })
  })

  describe('radio buttons', () => {
    it('should work correctly', () => {
      for (const inputDebugElement of fixture.debugElement.queryAll(By.css('input[type="radio"]'))) {
        const input: HTMLInputElement = inputDebugElement.nativeElement
        const label: HTMLElement = input.parentElement
        const name = input.name
        const value = input.value

        delete remainingOptions[name]

        label.click()
        fixture.detectChanges()

        const cy = fixture.componentInstance.cytoscapeComponent.cy
        expect(getOptionFromCytoscape(cy, name)).toEqual(value)
      }
    })
  })

  it('should have tests covering all cytoscape options', () => {
    // -------------------- THIS TEST NEEDS TO BE LAST --------------------
    // This test verifies that all options were properly represented in the
    // templates. Due to inter-dependent tests, this NEEDS to go last.
    expect(Object.keys(remainingOptions).length).toEqual(0)
  })
})

@Component({
  template: `
    <ts-graphs-cytoscape-settings [settings]="settings">
    </ts-graphs-cytoscape-settings>
    <ts-graphs-cytoscape
      [minZoom]="settings.minZoom"
      [maxZoom]="settings.maxZoom"
      [zoomingEnabled]="settings.zoomingEnabled"
      [userZoomingEnabled]="settings.userZoomingEnabled"
      [panningEnabled]="settings.panningEnabled"
      [userPanningEnabled]="settings.userPanningEnabled"
      [boxSelectionEnabled]="settings.boxSelectionEnabled"
      [selectionType]="settings.selectionType"
      [touchTapThreshold]="settings.touchTapThreshold"
      [desktopTapThreshold]="settings.desktopTapThreshold"
      [autolock]="settings.autolock"
      [autoungrabify]="settings.autoungrabify"
      [autounselectify]="settings.autounselectify"

      [headless]="settings.headless"
      [styleEnabled]="settings.styleEnabled"
      [hideEdgesOnViewport]="settings.hideEdgesOnViewport"
      [hideLabelsOnViewport]="settings.hideLabelsOnViewport"
      [textureOnViewport]="settings.textureOnViewport"
      [motionBlur]="settings.motionBlur"
      [motionBlurOpacity]="settings.motionBlurOpacity"
      [wheelSensitivity]="settings.wheelSensitivity"
      [pixelRatio]="settings.pixelRatio"
    ></ts-graphs-cytoscape>
  `,
})
class SettingsTestComponent {
  @ViewChild(CytoscapeComponent) cytoscapeComponent: CytoscapeComponent
  @ViewChild(CytoscapeSettingsComponent) cytoscapeSettingsComponent: CytoscapeSettingsComponent
  settings = {...testCytoscapeOptions}
}
