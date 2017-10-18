import {Observable} from 'rxjs'
import {HttpEvent, HttpInterceptor, HttpHandler, HttpRequest} from '@angular/common/http'

export class AttachCsrfTokenInterceptor implements HttpInterceptor {
  intercept(request: HttpRequest<{}>, httpHandler: HttpHandler): Observable<HttpEvent<any>> {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')['content']
    const fixedRequest = request.clone({
      headers: request.headers.set('X-CSRFToken', csrfToken),
    })
    return httpHandler.handle(fixedRequest)
  }
}
