import {TestBed, ComponentFixture} from '@angular/core/testing';
import {BrowserDynamicTestingModule, platformBrowserDynamicTesting} from '@angular/platform-browser-dynamic/testing';
import {BrowserModule, By} from '@angular/platform-browser';
import {FormsModule} from '@angular/forms';
import {CypherQueryComponent} from './cypher-query.component';

describe('CypherQueryComponent', () => {

  beforeAll(() => {
    TestBed.resetTestEnvironment();
    TestBed.initTestEnvironment(
      BrowserDynamicTestingModule, platformBrowserDynamicTesting(),
    );
  });

  let fixture: ComponentFixture<CypherQueryComponent>;

  beforeEach(async () => {
    TestBed.configureTestingModule({
      imports: [BrowserModule, FormsModule],
      declarations: [CypherQueryComponent],
    });
    fixture = TestBed.createComponent(CypherQueryComponent);
    fixture.detectChanges();
    await fixture.whenStable();
  });

  describe('.cypherSearch', () => {
    let textbox: HTMLInputElement;
    let form: HTMLFormElement;
    let submit: HTMLElement;
    let cypherSearchPromise: Promise<string>;

    beforeEach(() => {
      textbox = fixture.debugElement.query(By.css('input[type="search"]')).nativeElement;
      form = fixture.debugElement.query(By.css('form')).nativeElement;
      submit = fixture.debugElement.query(By.css('[type="submit"]')).nativeElement;
      cypherSearchPromise = fixture.componentInstance.cypherSearch.first().toPromise();

      textbox.value = 'MATCH (a) RETURN (a)';
      textbox.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    });

    it('should be emitted when user submits the form', async () => {
      form.dispatchEvent(new Event('submit'));
      fixture.detectChanges();

      const cypherSearch = await cypherSearchPromise;
      expect(cypherSearch).toEqual('MATCH (a) RETURN (a)');
    });

    it('should be emitted when user presses search button', async () => {
      submit.click();
      fixture.detectChanges();

      const cypherSearch = await cypherSearchPromise;
      expect(cypherSearch).toEqual('MATCH (a) RETURN (a)');
    });
  });
});
