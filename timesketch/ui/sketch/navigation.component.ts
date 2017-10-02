import {Component, Input} from '@angular/core'

@Component({
  selector: 'ts-sketch-navigation',
  templateUrl: './navigation.component.html',
})
export class NavigationComponent {
  @Input() sketchId: number
  @Input() active: string
  @Input("graphsEnabled") graphsEnabledString: 'True' | 'False'

  get graphsEnabled(): boolean {
    return this.graphsEnabledString === 'True'
  }
}
