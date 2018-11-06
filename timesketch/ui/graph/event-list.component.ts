import {Component, Input, ChangeDetectorRef} from '@angular/core';

import {SketchService} from '../api/sketch.service';
import {Event} from './models';

@Component({
  selector: 'ts-graphs-event-list',
  templateUrl: './event-list.component.html',
})
export class EventListComponent {
  events?: Event[];
  private _query = '';
  local_query: string;

  constructor(
    private readonly sketchService: SketchService,
    private readonly changeDetectorRef: ChangeDetectorRef,
  ) {}

  @Input()
  set query(query: string) {
    this._query = query;
    this.local_query = query;
    delete this.events;
    this.sketchService.search(query).subscribe((events) => {
      this.events = events;
      this.changeDetectorRef.detectChanges();
    });
  }

  get query() {
    return this._query;
  }

  onSubmit() {
    this.query = this.local_query;
  }
}
