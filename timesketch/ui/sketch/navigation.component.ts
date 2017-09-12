import {Component, Input} from '@angular/core'

@Component({
  selector: 'ts-sketch-navigation',
  templateUrl: './navigation.component.html',
})
export class NavigationComponent {
  @Input() sketchId: number
  @Input() active: string
}
