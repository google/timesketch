import {Component, Input} from '@angular/core';

import {SketchService} from '../api/sketch.service';
import {Timeline} from '../api/models';
import {Event} from './models';

@Component({
  selector: 'ts-graphs-event',
  templateUrl: './event.component.html',
})
export class EventComponent {
  @Input() event: Event;
  showDetails = false;

  constructor(private readonly sketchService: SketchService) {}

  get timeline(): Timeline {
    return this.sketchService.getTimelineFromIndexName(this.event._index);
  }

  stringify(event) {
    return JSON.stringify(event).slice(0, 80);
  }

  get hasStar(): boolean {
    return this.event._source.label.indexOf('__ts_star') > -1;
  }

  get hasComment(): boolean {
    return this.event._source.label.indexOf('__ts_comment') > -1;
  }

  toggleDetails() {
    this.showDetails = !this.showDetails;
  }
}
