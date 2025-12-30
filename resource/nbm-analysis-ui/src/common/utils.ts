export function inIframe() {
  try {
    return window.self !== window.top
  } catch (e) {
    console.log(e)
    return true
  }
}

export const checkIfArrOrString = function (x: string | string[]) {
  let outputSring: string
  if (Array.isArray(x)) {
    outputSring = x[0]
  } else {
    outputSring = x
  }
  return outputSring
}

export function getURLChildElement(path: string) {
  return path.substring(path.lastIndexOf('/') + 1)
}

export const surveyIdAlphaNumLength = 12

export function getAlphaNumericString() {
  return Math.random()
    .toString(20)
    .slice(2, surveyIdAlphaNumLength + 2)
}

export function isStringSurveyId(s: string) {
  const res = s.split('-')
  if (res.length === 2) {
    const surveyIndicator = res[0]
    const uniqueId = res[1]
    if (
      uniqueId.length == surveyIdAlphaNumLength &&
      surveyIndicator === 'survey'
    ) {
      return true
    }
  }
  return false
}

export function getCurrentDateTime() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const day = now.getDate()
  const hour = now.getHours()
  const minutes = now.getMinutes()

  const formattedDate = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')} ${hour.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`

  return formattedDate
}

export function getDeepCopy(obj: object) {
  return JSON.parse(JSON.stringify(obj))
}
