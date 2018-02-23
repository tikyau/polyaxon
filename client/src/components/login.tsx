import * as React from 'react';

export interface Props {
  next: string | null;
  login: (username: string, password: string) => any;
  history: any;
}

export default class Login extends React.Component<Props, Object> {

  handleSubmit = (event: any) => {
    event.preventDefault();
    let username = (document.getElementById('username') as HTMLInputElement).value;
    let password = (document.getElementById('password') as HTMLInputElement).value;

    this.props.login(username, password).then((resp: any) => {
      if (this.props.next) {
        this.props.history.push(this.props.next);
      } else {
        this.props.history.push(`/${username}/`);
      }
    }).catch((err: string) => {
      (
        document.getElementById('error-message') as HTMLElement
      ).innerHTML = 'Unable to log in with provided credentials.';
    });
  };

  public render() {
    return (
      <div className="row">
        <div className="col-md-6 col-md-offset-3 login-form">
          <div className="login">
            <form onSubmit={this.handleSubmit}>
              <div className="form-group">
                <label>Username or Email</label>
                <input type="text" className="form-control" id="username" placeholder="Username"/>
              </div>
              <div className="form-group">
                <label>Password</label>
                <input type="password" className="form-control" id="password"/>
              </div>
              <div className="submit">
                <input type="submit" value="Login" className="button btn btn-polyaxon"/>
              </div>
              <div className="bg-danger error-message" id="error-message"/>
            </form>
          </div>
        </div>
      </div>
    );
  }
}
