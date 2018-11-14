import {Component, Input} from '@angular/core';

@Component({
  selector: 'ts-sketch-navigation',
  templateUrl: './navigation.component.html',
})
export class NavigationComponent {
  @Input() sketchId: number;
  @Input() active: string;
  // tslint:disable-next-line:no-input-rename
  @Input('graphsEnabled') graphsEnabledString: 'True' | 'False';

  get graphsEnabled(): boolean {
    return this.graphsEnabledString === 'True';
  }
}
