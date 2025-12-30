import axios from 'axios'
import type { AxiosInstance } from 'axios'


export class ServerAPIFactory {
  private _host: string
  public client: AxiosInstance

  constructor(host: string) {
    this._host = host
    this.client = axios.create({ baseURL: host })
  }

  public get host() {
    return this._host
  }

  public async getHelloWorld() {
    const responseData = await this.client.get<string>(
      'api/example/get_hello_world',
    )
    return responseData.data
  }


}
