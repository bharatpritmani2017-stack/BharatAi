from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class BharatAIApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical")
        layout.add_widget(Label(text="⚡ Bharat AI APK Working"))
        return layout

if __name__ == "__main__":
    BharatAIApp().run()