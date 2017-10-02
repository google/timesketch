import {async, TestBed, ComponentFixture} from '@angular/core/testing'
import {BrowserDynamicTestingModule, platformBrowserDynamicTesting} from '@angular/platform-browser-dynamic/testing'
import {BrowserModule} from '@angular/platform-browser'

import {NavigationComponent} from './navigation.component'

TestBed.initTestEnvironment(BrowserDynamicTestingModule, platformBrowserDynamicTesting())

describe('NavigationComponent', () => {

  let fixture: ComponentFixture<NavigationComponent>

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [BrowserModule],
      declarations: [NavigationComponent],
    })
    fixture = TestBed.createComponent(NavigationComponent)
  })

  const tabs = ['overview', 'explore', 'stories', 'views', 'timelines']

  for (const [tabIndex, tab] of tabs.entries()) {
    it(`should render navigation for the "${tab}" tab correctly`, async(() => {
      fixture.componentInstance.active = tab
      fixture.detectChanges()
      const navEntries = fixture.nativeElement.querySelectorAll('li')
      expect(navEntries.length).toEqual(tabs.length)
      for (const [navEntryIndex, navEntry] of navEntries.entries()) {
        if (navEntryIndex === tabIndex) {
          expect(navEntry.classList).toContain('active')
        } else {
          expect(navEntry.classList).not.toContain('active')
        }
      }
    }))
  }

})
