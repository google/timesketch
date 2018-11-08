import {
  Component, ViewChild, ElementRef, Input, Output, OnChanges, SimpleChanges, EventEmitter,
  AfterViewInit, OnDestroy, NgZone,
} from '@angular/core';
import * as cytoscape from 'cytoscape';

 type Opt = Cy.CytoscapeOptions;

interface CytoscapeEvent<T> {
  cy: Cy.Core;
  target: T;
  type: string;
  namespace: string;
  timeStamp: number;
}

interface CytoscapeLayoutEvent extends CytoscapeEvent<Cy.Core> {
  layout: Cy.Layouts;
}

interface CytoscapeInputEvent<E, T> extends CytoscapeEvent<T> {
  position: Cy.Position;
  renderedPosition: Cy.Position;
  originalEvent: E;
}

type Evt = {
  [K in keyof DocumentEventMap]: CytoscapeInputEvent<DocumentEventMap[K], Cy.Core | Cy.SingularElement>
} & {
  taphold: CytoscapeInputEvent<TouchEvent, Cy.Core | Cy.SingularElement>
  boxstart: CytoscapeInputEvent<Event, Cy.Core>
  boxend: CytoscapeInputEvent<Event, Cy.Core>
  boxselect: CytoscapeInputEvent<Event, Cy.SingularElement>
  box: CytoscapeInputEvent<Event, Cy.SingularElement>
  layoutstart: CytoscapeLayoutEvent
  layoutstop: CytoscapeLayoutEvent
  layoutready: CytoscapeLayoutEvent
  ready: CytoscapeEvent<Cy.Core>
  destroy: CytoscapeEvent<Cy.Core>
  render: CytoscapeEvent<Cy.Core>
  resize: CytoscapeEvent<Cy.Core>
};

const immutable_options = [
  'headless', 'styleEnabled', 'hideEdgesOnViewport', 'hideLabelsOnViewport',
  'textureOnViewport', 'motionBlur', 'touchTapThreshold',
  'desktopTapThreshold', 'motionBlurOpacity', 'wheelSensitivity',
  'pixelRatio', 'selectionType',
];

const mutable_options = [
  'elements', 'style', 'layout', 'zoom', 'pan', 'minZoom', 'maxZoom',
  'zoomingEnabled', 'userZoomingEnabled', 'panningEnabled',
  'userPanningEnabled', 'boxSelectionEnabled', 'autolock', 'autoungrabify',
  'autounselectify',
];

/**
 * Component that embeds Cytoscape. The component is intended to mirror
 * Cytoscape API, without any custom additions.
 *
 * Input properties correspond to Cytoscape
 * initialization options. They can be changed at any time and the changes will
 * be reflected. If an immutable option is changed, Cytoscape instance will be
 * rebuilt. Properties {@link CytoscapeComponent#zoom} and {@link CytoscapeComponent#pan}
 * can be two-way bound using the banana-in-box syntax.
 *
 * Output properties correspond to Cytoscape graph events and user input device
 * events. They are emitted as-is from Cytoscape, not wrapped in any way.
 * Exceptions are 'pan' and 'zoom' Cytoscape events, they should be handled
 * using panChange and zoomChange respectively.
 *
 * Maintenance instructions:
 * if a new initialization option is added to Cytoscape, the
 * following needs to be updated:
 *  - cytoscape.component.ts:
 *    - @Input() property needs to be added to CytoscapeComponent
 *    - its name has to be added either to mutable_options or to immutable_options
 *  - cytoscape.component.spec.ts:
 *    - something different than default value needs to be added to
 *      testCytoscapeOptions - to test if changes are properly reflected
 *    - template of OptionsTestComponent needs to be updated
 * if a new graph event or user input device event is added, the following
 * needs to be updated:
 *  - cytoscape.component.ts:
 *    - @Output() property needs to be added to CytoscapeComponent
 *    - type of this event needs to be added to Evt type map
 *  - cytoscape.component.spec.ts:
 *    - its name needs to be added to testCytoscapeEvents
 *    - template of EventsTestComponent needs to be updated
 * @see {@link http://js.cytoscape.org/#core/initialisation}
 */
@Component({
  selector: 'ts-graphs-cytoscape',
  template: '<div #cytoscapeHostElement></div>',
})
export class CytoscapeComponent implements OnChanges, AfterViewInit, OnDestroy {
  @ViewChild('cytoscapeHostElement')
  private cytoscapeHostRef: ElementRef;
  private _cy: Cy.Core;

  /**
   * Reference to Cytoscape instance. This is a readonly property and it might
   * change during the lifetime of this component, so references to it should
   * not be saved anywhere.
   */
  get cy(): Cy.Core {
    return this._cy;
  }

  constructor(private zone: NgZone) {}

  // tslint:disable:no-unused-variable

  // very commonly used options
  @Input() elements?: Opt['elements'];
  @Input() style?: Opt['style'];
  @Input() layout?: Opt['layout'];

  // viewport state
  @Input() zoom?: Opt['zoom'];
  @Output() zoomChange = new EventEmitter<Opt['zoom']>();
  @Input() pan?: Opt['pan'];
  @Output() panChange = new EventEmitter<Opt['pan']>();

  // interaction options
  @Input() minZoom?: Opt['minZoom'];
  @Input() maxZoom?: Opt['maxZoom'];
  @Input() zoomingEnabled?: Opt['zoomingEnabled'];
  @Input() userZoomingEnabled?: Opt['userZoomingEnabled'];
  @Input() panningEnabled?: Opt['panningEnabled'];
  @Input() userPanningEnabled?: Opt['userPanningEnabled'];
  @Input() boxSelectionEnabled?: Opt['boxSelectionEnabled'];
  @Input() selectionType?: Opt['selectionType'];
  @Input() touchTapThreshold?: Opt['touchTapThreshold'];
  @Input() desktopTapThreshold?: Opt['desktopTapThreshold'];
  @Input() autolock?: Opt['autolock'];
  @Input() autoungrabify?: Opt['autoungrabify'];
  @Input() autounselectify?: Opt['autounselectify'];

  // rendering options
  @Input() headless?: Opt['headless'];
  @Input() styleEnabled?: Opt['styleEnabled'];
  @Input() hideEdgesOnViewport?: Opt['hideEdgesOnViewport'];
  @Input() hideLabelsOnViewport?: Opt['hideLabelsOnViewport'];
  @Input() textureOnViewport?: Opt['textureOnViewport'];
  @Input() motionBlur?: Opt['motionBlur'];
  @Input() motionBlurOpacity?: Opt['motionBlurOpacity'];
  @Input() wheelSensitivity?: Opt['wheelSensitivity'];
  @Input() pixelRatio?: Opt['pixelRatio'];

  // user input device events
  @Output() mousedown = new EventEmitter<Evt['mousedown']>();
  @Output() mouseup = new EventEmitter<Evt['mouseup']>();
  @Output() click = new EventEmitter<Evt['click']>();
  @Output() mouseover = new EventEmitter<Evt['mouseover']>();
  @Output() mouseout = new EventEmitter<Evt['mouseout']>();
  @Output() mousemove = new EventEmitter<Evt['mousemove']>();
  @Output() touchstart = new EventEmitter<Evt['touchstart']>();
  @Output() touchmove = new EventEmitter<Evt['touchmove']>();
  @Output() touchend = new EventEmitter<Evt['touchend']>();

  // higher-level user input device events
  @Output() tapstart = new EventEmitter<Evt['mousedown' | 'touchstart']>();
  @Output() vmousedown = new EventEmitter<Evt['mousedown' | 'touchstart']>();
  @Output() tapdrag = new EventEmitter<Evt['touchmove' | 'mousemove']>();
  @Output() vmousemove = new EventEmitter<Evt['touchmove' | 'mousemove']>();
  @Output() tapdragover = new EventEmitter<Evt['touchmove' | 'mousemove' | 'mouseover']>();
  @Output() tapdragout = new EventEmitter<Evt['touchmove' | 'mousemove' | 'mouseout']>();
  @Output() tapend = new EventEmitter<Evt['mouseup' | 'touchend']>();
  @Output() vmouseup = new EventEmitter<Evt['mouseup' | 'touchend']>();
  @Output() tap = new EventEmitter<Evt['click' | 'touchend']>();
  @Output() vclick = new EventEmitter<Evt['click' | 'touchend']>();
  @Output() taphold = new EventEmitter<Evt['taphold']>();
  @Output() cxttapstart = new EventEmitter<Evt['mousedown' | 'touchstart']>();
  @Output() cxttapend = new EventEmitter<Evt['mouseup' | 'touchend']>();
  @Output() cxttap = new EventEmitter<Evt['click' | 'touchend']>();
  @Output() cxtdrag = new EventEmitter<Evt['touchmove' | 'mousemove']>();
  @Output() cxtdragover = new EventEmitter<Evt['touchmove' | 'mousemove' | 'mouseover']>();
  @Output() cxtdragout = new EventEmitter<Evt['touchmove' | 'mousemove' | 'mouseout']>();
  @Output() boxstart = new EventEmitter<Evt['boxstart']>();
  @Output() boxend = new EventEmitter<Evt['boxend']>();
  @Output() boxselect = new EventEmitter<Evt['boxselect']>();
  @Output() box = new EventEmitter<Evt['box']>();

  // graph events
  @Output() layoutstart = new EventEmitter<Evt['layoutstart']>();
  @Output() layoutready = new EventEmitter<Evt['layoutready']>();
  @Output() layoutstop = new EventEmitter<Evt['layoutstop']>();
  @Output() ready = new EventEmitter<Evt['ready']>();
  @Output() destroy = new EventEmitter<Evt['destroy']>();
  @Output() render = new EventEmitter<Evt['render']>();
  @Output() resize = new EventEmitter<Evt['resize']>();

  // tslint:enable:no-unused-variable

  initCytoscape() {
    const all_options = [].concat(immutable_options, mutable_options);
    const options: Opt = {};
    if (this.cytoscapeHostRef) {
      options['container'] = this.cytoscapeHostRef.nativeElement;
    }
    for (const k of all_options) {
      options[k] = this[k];
    }
    this._cy = this.zone.runOutsideAngular(() => cytoscape(options));
    this.initEvents();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (!this.cy) return;
    const changed = (k) =>
      k in changes && changes[k].previousValue !== changes[k].currentValue;
    const options: Opt = {};
    let needs_rebuild = false;
    for (const k of Object.keys(changes)) {
      if (changed(k)) {
        options[k] = changes[k].currentValue;
      }
      if (immutable_options.indexOf(k) > -1 && this.cy) {
        needs_rebuild = true;
        break;
      }
    }
    if (needs_rebuild) {
      this.cy.destroy();
      this._cy = undefined;
      this.initCytoscape();
    } else {
      (this.cy.json as any)(options);
      if (changed('layout')) {
        const layout: any = this.cy.layout(this.layout as Cy.LayoutOptions);
        layout.run();
      }
    }
  }

  ngAfterViewInit() {
    this.initCytoscape();
  }

  private initEvents() {
    this.cy.on('pan', () => {
      this.pan = this.cy.pan();
      this.panChange.emit(this.pan);
    });
    this.cy.on('zoom', () => {
      this.zoom = this.cy.zoom();
      this.zoomChange.emit(this.zoom);
    });
    // in some cases the 'ready' cytoscape event is emitted before this line of code is executed,
    // so we use cy.ready(...) to ensure that angular event CytoscapeComponent.ready is always emitted
    this.cy.ready((e) => this.ready.emit(e));
    for (const [k, v] of Object.entries(this)) {
      if (v instanceof EventEmitter && !k.endsWith('Change') && k !== 'ready') {
        this.cy.on(k, (e) => v.emit(e));
      }
    }
  }

  ngOnDestroy() {
    this.cy.destroy();
  }
}
