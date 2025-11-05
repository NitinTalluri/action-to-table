import RobotoBlackItalic from "~/fonts/Roboto/Roboto-BlackItalic.ttf";
import RobotoBold from "~/fonts/Roboto/Roboto-Bold.ttf";
import RobotoBoldItalic from "~/fonts/Roboto/Roboto-BoldItalic.ttf";
import RobotoItalic from "~/fonts/Roboto/Roboto-Italic.ttf";
import RobotoLight from "~/fonts/Roboto/Roboto-Light.ttf";
import RobotoLightItalic from "~/fonts/Roboto/Roboto-LightItalic.ttf";
import RobotoMedium from "~/fonts/Roboto/Roboto-Medium.ttf";
import RobotoMediumItalic from "~/fonts/Roboto/Roboto-MediumItalic.ttf";
import RobotoRegular from "~/fonts/Roboto/Roboto-Regular.ttf";
import RobotoThin from "~/fonts/Roboto/Roboto-Thin.ttf";
import RobotoThinItalic from "~/fonts/Roboto/Roboto-ThinItalic.ttf";

export type TFontType = {
  fontFamily: string;
  fontStyle: string;
  fontWeight: number | string;
  src: string[];
  format: string[];
  unicodeRange: string;
};

const toFontFace = (font: TFontType): string => {
  const srcs = font.src
    .map((src, index) => `url(${src}) format('${font.format[index]}')`)
    .join(", ");

  return `
  @font-face {
    font-family: '${font.fontFamily}';
    font-style: ${font.fontStyle};
    font-display: swap;
    font-weight: ${font.fontWeight};
    src: ${srcs}, local('${font.fontFamily}');
    unicodeRange: ${font.unicodeRange};
  }
  `;
};

export const convertFonts = (fonts: TFontType[]): string => {
  return fonts.map(toFontFace).join("\n");
};

const robotoNormalFont = {
  fontFamily: "Roboto",
  fontStyle: "normal",
  fontWeight: "400",
  src: [RobotoRegular],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};
const robotoThinFont = {
  fontFamily: "Roboto",
  fontStyle: "normal",
  fontWeight: "100",
  src: [RobotoThin],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

const robotoLightFont = {
  fontFamily: "Roboto",
  fontStyle: "normal",
  fontWeight: "300",
  src: [RobotoLight],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

const robotoMediumFont = {
  fontFamily: "Roboto",
  fontStyle: "normal",
  fontWeight: "500",
  src: [RobotoMedium],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

const robotoBoldFont = {
  fontFamily: "Roboto",
  fontStyle: "normal",
  fontWeight: "700",
  src: [RobotoBold],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

const robotoNormalItalicFont = {
  fontFamily: "Roboto",
  fontStyle: "italic",
  fontWeight: "400",
  src: [RobotoItalic],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};
const robotoThinItalicFont = {
  fontFamily: "Roboto",
  fontStyle: "italic",
  fontWeight: "100",
  src: [RobotoThinItalic],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

const robotoLightItalicFont = {
  fontFamily: "Roboto",
  fontStyle: "italic",
  fontWeight: "300",
  src: [RobotoLightItalic],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

const robotoMediumItalicFont = {
  fontFamily: "Roboto",
  fontStyle: "italic",
  fontWeight: "500",
  src: [RobotoMediumItalic],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

const robotoBoldItalicFont = {
  fontFamily: "Roboto",
  fontStyle: "italic",
  fontWeight: "700",
  src: [RobotoBoldItalic],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

const robotoBlackItalicFont = {
  fontFamily: "Roboto",
  fontStyle: "italic",
  fontWeight: "900",
  src: [RobotoBlackItalic],
  format: ["truetype"],
  unicodeRange:
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
};

export const fontFaces = convertFonts([
  robotoNormalFont,
  robotoThinFont,
  robotoLightFont,
  robotoMediumFont,
  robotoBoldFont,
  robotoNormalItalicFont,
  robotoThinItalicFont,
  robotoLightItalicFont,
  robotoMediumItalicFont,
  robotoBoldItalicFont,
  robotoBlackItalicFont,
]);
