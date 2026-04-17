export default [//左侧边栏
{ text: '快速导航', link: 'contents' },
{
text: '战队介绍',
collapsed: false,
items: [
{ text: '赛事介绍', link: '/Ambition_Introduction/competition_introduction' },
{ text: '战队简介', link: '/Ambition_Introduction/team_introduction' },
{ text: '参赛战绩', link: '/Ambition_Introduction/participation_history' },
{ text: '战队合照', link: '/Ambition_Introduction/team_photos' },
{ text: '战队成员', link: '/Ambition_Introduction/team_members' },
{ text: '兵种图片', link: '/Ambition_Introduction/robot_photo' },
{ text: '宣传视频', link: '/Ambition_Introduction/promotional_video' }
]
},
{
text: '战队历史',
collapsed: true,
items: [
{ text: '发展历程', link: '/History/history1' },
]
},
{
text: '加入我们',
collapsed: false,
items: [
{ text: '招新介绍', link: '/Sign_Up/sign_up_introduction' },
{ text: '组别介绍', link: '/Sign_Up/group_introduction' },
{ text: 'Q&A', link: '/Sign_Up/QA' }
]
},
{
text: '照片展示',
collapsed: true,
items: [
{ text: '17 对抗赛', link: '/Photo/17DKS' },
{ text: '18 对抗赛', link: '/Photo/18DKS' },
{ text: '19 对抗赛', link: '/Photo/19DKS' },
{ text: '21 联盟赛', link: '/Photo/21LMS' },
{ text: '21 对抗赛', link: '/Photo/21DKS' },
{ text: '23 联盟赛', link: '/Photo/23LMS' },
{ text: '23 对抗赛', link: '/Photo/23DKS' },
{ text: '23 复活赛', link: '/Photo/23FHS' },
{ text: '24 联盟赛', link: '/Photo/24LMS' },
{ text: '24 对抗赛', link: '/Photo/24DKS' },
{ text: '25 对抗赛', link: '/Photo/25DKS' },
]
},
{
text: '知识库',
collapsed: true,
items: [
{ text: 'SW 安装指南', link: '/Knowledge/jx_sw' },
{ text: 'RM 操作手端使用', link: '/Knowledge/rm_server' },
]
},
{//置底，要添加目录在上面添加
text: '关于',
collapsed: true,
items: [
{ text: '官网项目组', link: '/team' },
]
},
]
