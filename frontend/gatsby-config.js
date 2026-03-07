```javascript
module.exports = {
  siteMetadata: {
    title: `TickerPulse AI v3.0`,
    description: `Multi-agent AI stock research and monitoring dashboard`,
  },
  plugins: [
    {
      resolve: `gatsby-plugin-react-i18next`,
      options: {
        i18next: require(`i18next`),
        reactI18next: require(`react-i18next`),
      },
    },
    {
      resolve: `gatsby-plugin-react-helmet`,
      options: {
        linkTags: false,
        meta: [
          {
            name: `description`,
            content: `Multi-agent AI stock research and monitoring dashboard`,
          },
        ],
        link: [],
      },
    },
  ],
};
```