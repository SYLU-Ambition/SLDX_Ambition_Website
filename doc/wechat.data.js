import fs from 'fs'
import path from 'path'

const ARTICLES_DIR = path.resolve('doc/public/wechat/articles')
const METADATA_JSON = path.resolve('doc/public/wechat/wechat-metadata.json')

const SKIP_ARTICLES = [
  '2026-05-22_公众号运营回归个人通知',
  '2025-09-15_我们搬家啦',
  '2025-06-03_沈理电协Ambition战队官网发布',
  '2025-06-18_大疆_2026_校招',
  '2024-06-13_大疆_2025',
  '2024-07-04_DJI_大疆',
  '2024-07-07_测一测你来_DJI',
  '2022-04-25_下一场，去大疆',
  '2018-04-13_DJI大疆创新RoboMaster机器人夏令营',
  '2018-03-09_RoboMaster2018最全招聘',
]

function shouldSkip(dirName) {
  if (SKIP_ARTICLES.some(s => dirName.startsWith(s))) return true
  const title = dirName.slice(11)
  if (title.startsWith('转载') || title.startsWith('转载_')) return true
  return false
}

function extractTitle(htmlPath) {
  try {
    const content = fs.readFileSync(htmlPath, 'utf-8')
    const match = content.match(/<title>(.*?)<\/title>/)
    if (match) {
      return match[1]
        .trim()
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#x27;/g, "'")
        .replace(/&#(\d+);/g, (_, d) => String.fromCharCode(d))
    }
  } catch {}
  return null
}

function scanDirectories() {
  const articles = []
  try {
    const dirs = fs.readdirSync(ARTICLES_DIR, { withFileTypes: true })
    for (const entry of dirs) {
      if (!entry.isDirectory() || entry.name.startsWith('_')) continue
      const dateMatch = entry.name.match(/^(\d{4}-\d{2}-\d{2})_/)
      if (!dateMatch) continue
      const date = dateMatch[1]
      const year = parseInt(date.slice(0, 4))
      if (shouldSkip(entry.name)) continue
      const htmlPath = path.join(ARTICLES_DIR, entry.name, 'index.html')

      const coverJpg = path.join(ARTICLES_DIR, entry.name, 'cover.jpg')
      const coverPng = path.join(ARTICLES_DIR, entry.name, 'cover.png')
      const coverWebp = path.join(ARTICLES_DIR, entry.name, 'cover.webp')
      const hasCover = fs.existsSync(coverJpg) || fs.existsSync(coverPng) || fs.existsSync(coverWebp)
      let coverExt = null
      if (fs.existsSync(coverJpg)) coverExt = 'jpg'
      else if (fs.existsSync(coverPng)) coverExt = 'png'
      else if (fs.existsSync(coverWebp)) coverExt = 'webp'

      let hasVideo = false
      try {
        const html = fs.readFileSync(htmlPath, 'utf-8')
        hasVideo = /<video\b|<mpvideo\b|video_\w+\.mp4|v\.qq\.com/.test(html)
      } catch {}

      let title = null
      if (fs.existsSync(htmlPath)) {
        title = extractTitle(htmlPath)
      }
      if (!title) {
        title = entry.name.slice(11).replace(/_/g, ' ')
      }

      articles.push({
        date,
        year,
        title,
        dir: entry.name,
        hasCover,
        coverExt,
        hasVideo
      })
    }
  } catch (e) {
    console.error('Failed to scan articles:', e)
  }
  articles.sort((a, b) => b.date.localeCompare(a.date))
  return articles
}

export default {
  async load() {
    let articles = []

    if (fs.existsSync(METADATA_JSON)) {
      try {
        const jsonData = JSON.parse(fs.readFileSync(METADATA_JSON, 'utf-8'))
        articles = jsonData
          .filter(a => !shouldSkip(a.dir))
          .map(a => ({
          date: a.date,
          year: a.year || parseInt(a.date.slice(0, 4)),
          title: a.title,
          dir: a.dir,
          hasCover: a.hasCover || false,
          coverExt: a.coverExt || 'jpg',
          hasVideo: a.hasVideo || false
        }))
      } catch {
        articles = scanDirectories()
      }
    } else {
      articles = scanDirectories()
    }

    const years = [...new Set(articles.map(a => a.year))].sort((a, b) => b - a)
    return { articles, years }
  }
}
