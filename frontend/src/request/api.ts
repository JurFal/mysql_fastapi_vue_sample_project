import instance from "@/request/http";
import loginInstance from "@/request/http_login"

//一般情况下，接口类型会放到一个文件
// 下面两个TS接口，表示要传的参数
interface ReqLogin {
    username: string
    password: string
}
interface ResLogin {
    access_token: string
}

interface ReqRegister {
    username: string
    email: string
    first_name: string
    last_name: string
    password: string
    avatar: string
}


// Res是返回的参数，T是泛型，需要自己定义，返回对数统一管理***
type Res<T> = Promise<ItypeAPI<T>>;
// 一般情况下响应数据返回的这三个参数，
// 但不排除后端返回其它的可能性，
interface ItypeAPI<T> {
    success: string | null // 返回状态码的信息，如请求成功等;
    result: T,//请求的数据，用泛型
    msg: string | null // 返回状态码的信息，如请求成功等
    message:string
    code: number //返回后端自定义的200，404，500这种状态码
    user: User
    users: User[]
    total_users: number
    total_pages: number
}

interface User {
    username: string
    email: string
    first_name: string
    last_name: string
    is_active: boolean
    is_superuser: boolean
    avatar: string
}

interface UserList {
    total: number
    users: User[]
}

interface Message {
    role: string
    content: string
}

interface LLMRequest {
    messages: Message[]
}

interface Choice {
  index: number
  message: {
    role: string
    content: string
  }
  finish_reason: string
}

interface Usage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

interface LLMResponse {
  id: string
  object: string
  created: number
  model: string
  system_fingerprint: string
  choices: Choice[]
  usage: Usage
  response?: string // 保留原有字段以兼容现有代码
}

//测试hello api
export const TestHello = (): Res<null> =>
    instance.get('/users_api/hello');

//登录 api
export const LoginApi = (data: ReqLogin): Promise<ResLogin> =>
    loginInstance.post('/users_api/token', data);

//注册 api
export const RegisterApi = (data: ReqRegister): Promise<User> =>
    instance.post('/users_api/users/', data);

//登出 api
export const LogoutApi = (): Res<null> =>
    instance.get('/users_api/logout');

//根据username查询用户信息api  get
export const GetUserInfoByUserName = (params: { userName: string }): Promise<User> =>
    instance.get(`/users_api/users/name/${params.userName}`);

export const GetUserInfoList = (params: { skip: number, limit: number }): Promise<UserList> =>
    instance.get(`/users_api/users/`, {params});

export const ChatWithLLM = (data: LLMRequest): Promise<LLMResponse> =>
    instance.post(`/api/chat/stream/`, data);


// 根据用户名删除用户
export const DeleteUserByUsername = (username: string) => {
  return instance.delete(`/users_api/users/name/${username}`);
};